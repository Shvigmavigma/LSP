
import random
import string
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from html import escape
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PROJECT_CHANGE_LABELS = {
    "admin_toggle_file_limits": "настройки ограничений файлов",
    "admin_update_project": "параметры проекта",
    "project_mark_old": "статус проекта: перенесен в архив",
    "project_unmark_old": "статус проекта: возвращен из архива",
    "join_request_create": "заявку на вступление в проект",
    "join_request_accept": "статус заявки на вступление: принята",
    "join_request_reject": "статус заявки на вступление: отклонена",
    "participant_remove": "состав участников проекта",
    "project_create": "создал проект",
    "project_full_update": "данные проекта",
    "tasks_bulk_update": "задачи проекта",
    "suggestion_create": "добавил предложение по проекту",
    "suggestion_accept": "статус предложения: принято",
    "suggestion_reject": "статус предложения: отклонено",
    "file_upload": "файлы проекта: добавлен файл",
    "file_delete": "файлы проекта: удален файл",
    "admin_delete_all_files": "файлы проекта: удалены все файлы",
    "project_hide_toggle": "видимость проекта",
    "admin_delete_project": "статус проекта: удален",
    "project_approval_request": "запрос на одобрение проекта",
    "project_approval_cancel": "запрос на одобрение проекта: отменен",
    "project_approval_decision": "решение по одобрению проекта",
}

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

async def send_project_notification_email(email: str, subject: str, body: str):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=f"<p>{body}</p>",
            subtype="html"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except Exception as e:
        print(f"Error sending project notification email: {e}")


async def send_project_change_notification_email(
    email: str,
    project_title: str,
    actor_name: str,
    changed_at: datetime,
    change_type: str,
    points: int,
):
    """Отправляет уведомление о значимом изменении проекта."""
    safe_project = escape(project_title)
    safe_actor = escape(actor_name)
    safe_description = escape(PROJECT_CHANGE_LABELS.get(change_type, change_type.replace("_", " ")))
    formatted_time = changed_at.strftime("%d.%m.%Y в %H:%M")
    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #242424; line-height: 1.6;">
      <p>Добрый день!</p>
      <p>В вашем проекте <strong>{safe_project}</strong> произошло значимое изменение.</p>
      <p>
        Пользователь <strong>{safe_actor}</strong><br>
        {formatted_time}<br>
        изменил: {safe_description}
      </p>
      <p style="color: #666;">Сложность изменения: {points} очков.</p>
    </div>
    """
    try:
        message = MessageSchema(
            subject=f"LSP: изменение в проекте «{project_title}»",
            recipients=[email],
            body=html_content,
            subtype="html",
        )
        await FastMail(conf).send_message(message)
    except Exception as e:
        print(f"Error sending project change notification to {email}: {e}")
