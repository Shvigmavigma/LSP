
import random
import string
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация для отправки 
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

def generate_verification_code(length: int = 6) -> str:
    """Генерирует код подтверждения из цифр"""
    return ''.join(random.choices(string.digits, k=length))

async def send_verification_email(email: str, code: str):
    """Отправляет код подтверждения на email"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Подтверждение email - LSP</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #42b983 0%, #2c7a4d 100%); padding: 30px 20px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">LSP</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Lyceum System of Projects</p>
                    </div>
                    
                    <!-- Body -->
                    <div style="padding: 30px 25px;">
                        <h2 style="color: #333; margin-top: 0; font-size: 22px;">Подтверждение email</h2>
                        <p style="color: #555; line-height: 1.6; font-size: 16px;">Здравствуйте!</p>
                        <p style="color: #555; line-height: 1.6; font-size: 16px;">Для завершения регистрации в сервисе <strong>LSP</strong> введите код подтверждения:</p>
                        
                        <div style="background-color: #f8f9fa; border-radius: 12px; padding: 20px; text-align: center; margin: 25px 0; border: 1px dashed #42b983;">
                            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #42b983; background: white; padding: 12px 24px; border-radius: 8px; display: inline-block;">{code}</span>
                        </div>
                        
                        <p style="color: #555; line-height: 1.6; font-size: 16px;">Код действителен в течение <strong>10 минут</strong>.</p>
                        <p style="color: #555; line-height: 1.6; font-size: 16px;">Если вы не регистрировались в LSP, просто проигнорируйте это письмо.</p>
                        
                        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 25px 0;">
                        
                        <p style="color: #777; font-size: 12px; text-align: center; margin-bottom: 0;">
                            LSP – платформа для управления проектами.<br>
                            © 2025 LSP. Все права защищены.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = MessageSchema(
            subject="Код подтверждения - LSP",
            recipients=[email],
            body=html_content,
            subtype="html"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"Email sent to {email} with code {code}")
    except Exception as e:
        print(f"Error sending email: {e}")
        # Резервный вывод кода в консоль
        print(f"\n=== Код подтверждения для {email} ===\n{code}\n=================================\n")

async def send_password_reset_email(email: str, token: str):
    """Отправляет ссылку для сброса пароля"""
    try:
        reset_link = f"http://localhost:5173/reset-password?token={token}"
        
        message = MessageSchema(
            subject="Сброс пароля - Система управления проектами",
            recipients=[email],
            body=f"""
            <h2>Сброс пароля</h2>
            <p>Для сброса пароля перейдите по ссылке:</p>
            <a href="{reset_link}">{reset_link}</a>
            <p>Ссылка действительна в течение 1 часа.</p>
            """,
            subtype="html"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        print(f"Error sending password reset email: {e}")