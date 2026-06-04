from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import httpx
import urllib.parse
import json
from database import session_local
from models import User
from auth import (
    create_access_token, 
    create_refresh_token, 
    get_current_user,
    get_password_hash,
    verify_password
)
from oauth_config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    GOOGLE_LINK_REDIRECT_URI
)
from core.memory_store import memory_store as redis_client
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["OAuth"])

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

# ============ Google OAuth - Вход ============

@router.get("/google/login")
async def google_login():
    """Начинает процесс OAuth с Google для входа"""
    state = secrets.token_urlsafe(32)
    redis_client.setex(f"oauth_state:{state}", 600, "login")
    
    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(GOOGLE_REDIRECT_URI)}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    logger.info(f"Google login initiated with state: {state}")
    return {"url": authorization_url}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Обрабатывает callback от Google для входа"""
    
    logger.info(f"Google callback received. State: {state}, Code: {code[:20]}...")
    
    # Проверяем state
    stored_state = redis_client.get(f"oauth_state:{state}")
    if not stored_state:
        logger.error(f"Invalid state: {state}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Invalid State</h2>
            <p>Security check failed. Please try logging in again.</p>
            <p><a href="http://localhost:5173/login">Back to login</a></p>
        </body>
        </html>
        """)
    redis_client.delete(f"oauth_state:{state}")
    
    # Обмениваем code на токены
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_REDIRECT_URI
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token error: {token_response.text}")
                return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>Error</title></head>
                <body style="font-family:sans-serif;text-align:center;padding:40px;">
                    <h2>❌ Token Error</h2>
                    <p>Failed to get authorization token from Google.</p>
                    <p>Error: {token_response.text[:200]}</p>
                    <p><a href="http://localhost:5173/login">Back to login</a></p>
                </body>
                </html>
                """)
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("No access token in response")
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>Error</title></head>
                <body style="font-family:sans-serif;text-align:center;padding:40px;">
                    <h2>❌ No Access Token</h2>
                    <p>Failed to receive access token from Google.</p>
                    <p><a href="http://localhost:5173/login">Back to login</a></p>
                </body>
                </html>
                """)
            
            # Получаем информацию о пользователе
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_info_response.status_code != 200:
                logger.error(f"User info error: {user_info_response.text}")
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>Error</title></head>
                <body style="font-family:sans-serif;text-align:center;padding:40px;">
                    <h2>❌ User Info Error</h2>
                    <p>Failed to get user information from Google.</p>
                    <p><a href="http://localhost:5173/login">Back to login</a></p>
                </body>
                </html>
                """)
            
            user_data = user_info_response.json()
            logger.info(f"User data received: {json.dumps(user_data, indent=2)}")
    
    except httpx.ConnectTimeout:
        logger.error("Connection timeout")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Connection Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>⚠️ Connection Timeout</h2>
            <p>Could not connect to Google servers.</p>
            <p>Please check your internet connection and try again.</p>
            <p><a href="http://localhost:5173/login">Back to login</a></p>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Unexpected Error</h2>
            <p>An unexpected error occurred: {str(e)}</p>
            <p><a href="http://localhost:5173/login">Back to login</a></p>
        </body>
        </html>
        """)
    
    google_id = user_data.get("sub")
    email = user_data.get("email")
    
    if not google_id or not email:
        logger.error(f"Incomplete user data. google_id: {google_id}, email: {email}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Incomplete User Data</h2>
            <p>Failed to get required user information from Google.</p>
            <p><a href="http://localhost:5173/login">Back to login</a></p>
        </body>
        </html>
        """)
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        logger.warning(f"User with google_id {google_id} not found")
        error_message = urllib.parse.quote(
            "Аккаунт Google не привязан. Сначала войдите через логин/пароль и привяжите Google в профиле."
        )
        frontend_url = f"http://localhost:5173/login?oauth_error={error_message}"
        
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Account Not Found</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                .container {{ text-align: center; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.1); max-width: 420px; }}
                .icon {{ font-size: 48px; margin-bottom: 16px; }}
                h2 {{ color: #d32f2f; margin-bottom: 12px; }}
                p {{ color: #666; margin-bottom: 8px; line-height: 1.5; }}
                .hint {{ font-size: 0.9rem; color: #999; margin-top: 16px; }}
            </style>
            <script>
                setTimeout(function() {{ window.location.href = "{frontend_url}"; }}, 5000);
            </script>
        </head>
        <body>
            <div class="container">
                <div class="icon">🔒</div>
                <h2>Google Account Not Linked</h2>
                <p>Your Google account is not linked to any account on this platform.</p>
                <p>Please sign in with your nickname/password first, then link Google in your profile settings.</p>
                <p class="hint">Redirecting back to login in 5 seconds...</p>
            </div>
        </body>
        </html>
        """)
    
    if not user.is_active:
        logger.warning(f"User {user.id} is banned")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Account Banned</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>🚫 Account Banned</h2>
            <p>Your account has been suspended. Please contact the administrator.</p>
        </body>
        </html>
        """)
    
    # Генерируем токены
    jwt_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    
    redis_client.setex(f"refresh:{user.id}:{refresh_token}", 7 * 24 * 60 * 60, "valid")
    
    frontend_url = f"http://localhost:5173/login?oauth_token={jwt_token}"
    
    logger.info(f"User {user.id} logged in via Google")
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Login Successful</title>
        <script>window.location.href = "{frontend_url}";</script>
    </head>
    <body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h2>✅ Login Successful!</h2>
        <p>Redirecting to application...</p>
    </body>
    </html>
    """)


# ============ Google OAuth - Привязка ============

@router.get("/link/google")  # ← ИЗМЕНИЛ POST на GET
async def link_google_account(
    current_user: User = Depends(get_current_user)
):
    """Начинает привязку Google аккаунта"""
    
    logger.info(f"User {current_user.id} initiating Google link")
    
    state = secrets.token_urlsafe(32)
    redis_client.setex(f"oauth_state:{state}", 600, f"link:{current_user.id}")
    
    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(GOOGLE_LINK_REDIRECT_URI)}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    logger.info(f"Google link URL generated for user {current_user.id}")
    return {"url": authorization_url}


@router.get("/google/link-callback")
async def google_link_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Обрабатывает callback для привязки Google"""
    
    logger.info(f"Google link callback received. State: {state}")
    
    state_data = redis_client.get(f"oauth_state:{state}")
    if not state_data:
        logger.error(f"Invalid state in link callback: {state}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Invalid State</h2>
            <p>Security check failed. Please try again.</p>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    redis_client.delete(f"oauth_state:{state}")
    
    if not state_data.startswith("link:"):
        logger.error(f"Invalid state data format: {state_data}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Invalid State Format</h2>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    
    user_id = int(state_data.split(":")[1])
    current_user = db.query(User).filter(User.id == user_id).first()
    
    if not current_user:
        logger.error(f"User {user_id} not found for Google link")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ User Not Found</h2>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    
    logger.info(f"Processing Google link for user {current_user.id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": GOOGLE_LINK_REDIRECT_URI
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token error in link: {token_response.text}")
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>Error</title></head>
                <body style="font-family:sans-serif;text-align:center;padding:40px;">
                    <h2>❌ Token Error</h2>
                    <p>Failed to get authorization token from Google.</p>
                    <p><a href="http://localhost:5173/profile">Back to profile</a></p>
                </body>
                </html>
                """)
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("No access token in link response")
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>Error</title></head>
                <body style="font-family:sans-serif;text-align:center;padding:40px;">
                    <h2>❌ No Access Token</h2>
                    <p><a href="http://localhost:5173/profile">Back to profile</a></p>
                </body>
                </html>
                """)
            
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_info_response.status_code != 200:
                logger.error(f"User info error in link: {user_info_response.text}")
                return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head><meta charset="UTF-8"><title>Error</title></head>
                <body style="font-family:sans-serif;text-align:center;padding:40px;">
                    <h2>❌ User Info Error</h2>
                    <p><a href="http://localhost:5173/profile">Back to profile</a></p>
                </body>
                </html>
                """)
            
            user_data = user_info_response.json()
            logger.info(f"Google user data for link: {json.dumps(user_data, indent=2)}")
    
    except httpx.ConnectTimeout:
        logger.error("Connection timeout in link callback")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Connection Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>⚠️ Connection Timeout</h2>
            <p>Please check your internet connection and try again.</p>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"Unexpected error in link callback: {str(e)}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Error</h2>
            <p>An error occurred: {str(e)}</p>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    
    google_id = user_data.get("sub")
    if not google_id:
        logger.error("No Google ID in user data")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ No Google ID</h2>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    
    # Проверяем, не привязан ли уже этот Google аккаунт
    existing_user = db.query(User).filter(
        User.google_id == google_id,
        User.id != current_user.id
    ).first()
    
    if existing_user:
        logger.warning(f"Google account {google_id} already linked to user {existing_user.id}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Already Linked</h2>
            <p>This Google account is already linked to another user.</p>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    
    # Привязываем Google
    current_user.google_id = google_id
    
    # Безопасно обновляем oauth_providers
    if current_user.oauth_providers is None:
        current_user.oauth_providers = ["google"]
    elif "google" not in current_user.oauth_providers:
        current_user.oauth_providers = current_user.oauth_providers + ["google"]
    
    try:
        db.commit()
        db.refresh(current_user)
        logger.info(f"Google account {google_id} linked to user {current_user.id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during Google link: {str(e)}")
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Error</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:40px;">
            <h2>❌ Database Error</h2>
            <p>Failed to save Google account link.</p>
            <p><a href="http://localhost:5173/profile">Back to profile</a></p>
        </body>
        </html>
        """)
    
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Account Linked</title>
        <script>window.location.href = "http://localhost:5173/profile?google_linked=true";</script>
    </head>
    <body style="font-family:sans-serif;text-align:center;padding:40px;">
        <h2>✅ Google Account Linked!</h2>
        <p>Redirecting to profile...</p>
    </body>
    </html>
    """)


# ============ Управление OAuth аккаунтами ============
from sqlalchemy import JSON
import json
@router.post("/unlink/google")
async def unlink_google_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отвязывает Google аккаунт"""
    
    try:
        # Используем прямой запрос для обновления
        db.query(User).filter(User.id == current_user.id).update({
            "google_id": None
        }, synchronize_session=False)
        
        db.commit()
        
        return {
            "message": "Google account unlinked successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def get_linked_providers(
    current_user: User = Depends(get_current_user)
):
    """Возвращает список привязанных OAuth провайдеров"""
    
    logger.info(f"Getting providers for user {current_user.id}")
    
    return {
        "providers": [
            {
                "provider": "google",
                "is_linked": bool(current_user.google_id),
                "email": current_user.email
            }
        ]
    }
