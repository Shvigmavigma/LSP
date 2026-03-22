# email_utils.py
import random
import string
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация для отправки email
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
        message = MessageSchema(
            subject="Код подтверждения - Система управления проектами",
            recipients=[email],
            body=f"""
            <h2>Подтверждение email</h2>
            <p>Ваш код подтверждения: <strong>{code}</strong></p>
            <p>Код действителен в течение 10 минут.</p>
            """,
            subtype="html"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"Email sent to {email} with code {code}")
    except Exception as e:
        print(f"Error sending email: {e}")
        # Для разработки - выводим код в консоль
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