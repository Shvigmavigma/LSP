from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
import httpx
from database import session_local
from models import User
from auth import (
    create_access_token, 
    create_refresh_token, 
    get_current_user,
    get_password_hash
)
from oauth_config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    GOOGLE_LINK_REDIRECT_URI
)
from core.memory_store import memory_store as redis_client
import secrets
from typing import Optional
import json

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
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    return {"url": authorization_url}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Обрабатывает callback от Google для входа"""
    
    # Проверяем state
    if not redis_client.get(f"oauth_state:{state}"):
        return HTMLResponse(content="<h1>Error</h1><p>Invalid state. Please try again.</p>")
    redis_client.delete(f"oauth_state:{state}")
    
    # Обмениваем code на токены
    async with httpx.AsyncClient() as client:
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
            return HTMLResponse(content=f"<h1>Error</h1><p>Failed to get token: {token_response.text}</p>")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Получаем информацию о пользователе
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_info_response.status_code != 200:
            return HTMLResponse(content="<h1>Error</h1><p>Failed to get user info from Google</p>")
        
        user_data = user_info_response.json()
    
    google_id = user_data.get("sub")
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    
    if not google_id or not email:
        return HTMLResponse(content="<h1>Error</h1><p>Failed to get required user info from Google</p>")
    
    # Ищем или создаем пользователя
    user = db.query(User).filter(
        (User.google_id == google_id) | (User.email == email)
    ).first()
    
    if user:
        # Обновляем google_id если его не было
        if not user.google_id:
            user.google_id = google_id
            if "google" not in (user.oauth_providers or []):
                user.oauth_providers = (user.oauth_providers or []) + ["google"]
            db.commit()
        
        if not user.is_active:
            return HTMLResponse(content="<h1>Error</h1><p>This account is banned. Please contact administrator.</p>")
    else:
        # Создаем нового пользователя
        nickname = f"google_{google_id[:8]}"
        user = User(
            nickname=nickname,
            fullname=name or "Google User",
            email=email,
            password=get_password_hash(secrets.token_urlsafe(32)),
            avatar=picture,
            is_active=True,
            is_verified=True,
            is_teacher=False,
            google_id=google_id,
            oauth_providers=["google"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Генерируем токены
    jwt_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    
    redis_client.setex(
        f"refresh:{user.id}:{refresh_token}", 
        7 * 24 * 60 * 60, 
        "valid"
    )
    
    # Возвращаем HTML, который редиректит на фронтенд
    frontend_url = f"http://localhost:5173/login?oauth_token={jwt_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Login Successful</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .container {{
                text-align: center;
                padding: 40px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.1);
            }}
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #4285F4;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            h2 {{ color: #333; }}
            p {{ color: #666; }}
        </style>
        <script>
            // Редиректим на фронтенд
            window.location.href = "{frontend_url}";
        </script>
    </head>
    <body>
        <div class="container">
            <h2>✅ Login Successful!</h2>
            <div class="spinner"></div>
            <p>Redirecting to application...</p>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


# ============ Google OAuth - Привязка ============

@router.post("/link/google")
async def link_google_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Начинает привязку Google аккаунта"""
    
    state = secrets.token_urlsafe(32)
    redis_client.setex(f"oauth_state:{state}", 600, f"link:{current_user.id}")
    
    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_LINK_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    return {"url": authorization_url}


@router.get("/google/link-callback")
async def google_link_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Обрабатывает callback для привязки Google"""
    
    # Проверяем state и получаем user_id
    state_data = redis_client.get(f"oauth_state:{state}")
    if not state_data:
        return HTMLResponse(content="<h1>Error</h1><p>Invalid state. Please try again.</p>")
    redis_client.delete(f"oauth_state:{state}")
    
    user_id = int(state_data.split(":")[1])
    current_user = db.query(User).filter(User.id == user_id).first()
    
    if not current_user:
        return HTMLResponse(content="<h1>Error</h1><p>User not found</p>")
    
    # Обмениваем code на токены
    async with httpx.AsyncClient() as client:
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
            return HTMLResponse(content=f"<h1>Error</h1><p>Failed to get token: {token_response.text}</p>")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Получаем информацию о пользователе
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_info_response.status_code != 200:
            return HTMLResponse(content="<h1>Error</h1><p>Failed to get user info from Google</p>")
        
        user_data = user_info_response.json()
    
    google_id = user_data.get("sub")
    if not google_id:
        return HTMLResponse(content="<h1>Error</h1><p>Failed to get Google ID</p>")
    
    # Проверяем, не привязан ли уже этот Google аккаунт
    existing_user = db.query(User).filter(
        User.google_id == google_id,
        User.id != current_user.id
    ).first()
    
    if existing_user:
        return HTMLResponse(content="<h1>Error</h1><p>This Google account is already linked to another user</p>")
    
    # Привязываем Google к текущему пользователю
    current_user.google_id = google_id
    if "google" not in (current_user.oauth_providers or []):
        current_user.oauth_providers = (current_user.oauth_providers or []) + ["google"]
    
    db.commit()
    
    # Возвращаем HTML, который редиректит на профиль
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Account Linked</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 24px rgba(0,0,0,0.1);
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #34A853;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            h2 { color: #34A853; }
            p { color: #666; }
        </style>
        <script>
            // Редиректим на страницу профиля
            window.location.href = "http://localhost:5173/profile?google_linked=true";
        </script>
    </head>
    <body>
        <div class="container">
            <h2>✅ Google Account Linked!</h2>
            <div class="spinner"></div>
            <p>Redirecting to profile...</p>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


# ============ Управление OAuth аккаунтами ============

@router.post("/unlink/google")
async def unlink_google_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отвязывает Google аккаунт"""
    
    current_user.google_id = None
    current_user.oauth_providers = [p for p in (current_user.oauth_providers or []) if p != "google"]
    
    db.commit()
    
    return {"message": "Google account unlinked successfully"}


@router.get("/providers")
async def get_linked_providers(
    current_user: User = Depends(get_current_user)
):
    """Возвращает список привязанных OAuth провайдеров"""
    
    return {
        "providers": [
            {
                "provider": "google",
                "is_linked": bool(current_user.google_id)
            }
        ]
    }