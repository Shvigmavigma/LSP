
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

PROJECT_FIELD_LABELS = {
    "title": "название",
    "class_key": "параллель",
    "direction_key": "направление",
    "body": "описание",
    "underbody": "дополнительное описание",
    "participants": "участники",
    "tasks": "задачи",
    "links": "ссылки",
    "comments": "комментарии",
    "suggestions": "предложения",
    "join_requests": "заявки на вступление",
    "lifecycle_state": "этап жизненного цикла",
    "file_quota_overrides": "персональные ограничения файлов",
    "required_roles": "необходимые роли",
    "is_hidden": "видимость проекта",
    "hidden_by": "кто скрыл проект",
    "hidden_by_users": "пользователи, скрывшие проект",
    "is_old": "архивный статус",
    "ignore_file_limits": "ограничения файлов",
    "is_approved": "одобрение проекта",
    "approval_status": "статус одобрения",
    "approval_requested_at": "время запроса на одобрение",
    "approval_requested_by": "автор запроса на одобрение",
    "approval_handled_at": "время решения по одобрению",
    "approval_handled_by": "кто принял решение по одобрению",
    "approval_comment": "комментарий к одобрению",
}

ROLE_LABELS = {
    "customer": "заказчик",
    "supervisor": "научный руководитель",
    "expert": "эксперт",
    "executor": "исполнитель",
    "curator": "куратор",
}

STATUS_LABELS = {
    "pending": "ожидает",
    "current": "текущий",
    "approval_pending": "ожидает подтверждения",
    "completed": "завершён",
    "accepted": "принято",
    "approved": "одобрено",
    "rejected": "отклонено",
    "draft": "черновик",
}

NESTED_FIELD_LABELS = {
    "id": "идентификатор",
    "user_id": "пользователь",
    "author_id": "автор",
    "authorId": "автор",
    "role": "роль",
    "requested_role": "запрошенная роль",
    "title": "название",
    "body": "описание",
    "content": "текст",
    "status": "статус",
    "progress": "прогресс",
    "timeline": "начало",
    "timelinend": "срок завершения",
    "assigned_to": "назначенный исполнитель",
    "current_stage_id": "текущий этап",
    "stages": "этапы",
    "comment": "комментарий",
    "changes": "предлагаемые изменения",
    "target_type": "объект предложения",
    "target_id": "идентификатор объекта",
    "github": "GitHub",
    "google_drive": "Google Диск",
    "project_limit": "лимит проекта",
    "user_limit": "лимит пользователя",
}


def readable_status(value) -> str:
    return STATUS_LABELS.get(str(value), str(value))


def readable_role(value) -> str:
    return ROLE_LABELS.get(str(value), str(value))


def format_scalar(value, field: str = "") -> str:
    if isinstance(value, bool):
        text = "да" if value else "нет"
    elif value is None or value == "":
        text = "не указано"
    elif field in {"role", "requested_role"}:
        text = readable_role(value)
    elif field == "status":
        text = readable_status(value)
    else:
        text = str(value)
    if len(text) > 300:
        text = f"{text[:300]}..."
    return escape(text)


def format_generic_value(value, field: str = "", depth: int = 0) -> str:
    """Преобразует неизвестную структуру в читаемый HTML без вывода JSON."""
    if depth >= 3 and isinstance(value, list):
        return f"элементов: {len(value)}"
    if depth >= 3 and isinstance(value, dict):
        return f"параметров: {len(value)}"
    if not isinstance(value, (dict, list)):
        return format_scalar(value, field)
    if isinstance(value, list):
        if not value:
            return "список пуст"
        items = [f"<li>{format_generic_value(item, depth=depth + 1)}</li>" for item in value[:8]]
        if len(value) > 8:
            items.append(f"<li>И ещё элементов: {len(value) - 8}.</li>")
        return f"<ul>{''.join(items)}</ul>"

    if not value:
        return "не указано"
    rows = []
    for key, nested_value in list(value.items())[:10]:
        label = escape(NESTED_FIELD_LABELS.get(key, key.replace("_", " ")))
        rendered = format_generic_value(nested_value, key, depth + 1)
        rows.append(f"<li><strong>{label}:</strong> {rendered}</li>")
    if len(value) > 10:
        rows.append(f"<li>И ещё параметров: {len(value) - 10}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_participants(value) -> str:
    if not value:
        return "участников нет"
    rows = []
    for participant in value[:12]:
        if not isinstance(participant, dict):
            rows.append(f"<li>{format_scalar(participant)}</li>")
            continue
        user_id = format_scalar(participant.get("user_id"))
        role = format_scalar(participant.get("role"), "role")
        rows.append(f"<li>Пользователь №{user_id}, роль: <strong>{role}</strong></li>")
    if len(value) > 12:
        rows.append(f"<li>И ещё участников: {len(value) - 12}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_tasks(value) -> str:
    if not value:
        return "задач нет"
    rows = []
    for task in value[:10]:
        if not isinstance(task, dict):
            rows.append(f"<li>{format_scalar(task)}</li>")
            continue
        title = format_scalar(task.get("title") or "Без названия")
        status = format_scalar(task.get("status"), "status")
        extras = []
        if task.get("progress") is not None:
            extras.append(f"прогресс: {format_scalar(task.get('progress'))}%")
        if task.get("timelinend"):
            extras.append(f"срок: {format_scalar(task.get('timelinend'))}")
        if task.get("assigned_to"):
            extras.append(f"исполнитель №{format_scalar(task.get('assigned_to'))}")
        suffix = f" ({'; '.join(extras)})" if extras else ""
        rows.append(f"<li><strong>{title}</strong> — статус: {status}{suffix}</li>")
    if len(value) > 10:
        rows.append(f"<li>И ещё задач: {len(value) - 10}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_links(value) -> str:
    if not value:
        return "ссылок нет"
    rows = []
    for key, link in value.items():
        label = escape(NESTED_FIELD_LABELS.get(key, key.replace("_", " ")))
        rows.append(f"<li><strong>{label}:</strong> {format_scalar(link)}</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_comments(value) -> str:
    if not value:
        return "комментариев нет"
    rows = []
    for comment in value[:8]:
        if not isinstance(comment, dict):
            rows.append(f"<li>{format_scalar(comment)}</li>")
            continue
        author = format_scalar(comment.get("authorId"))
        content = format_scalar(comment.get("content"))
        hidden = " (скрыт)" if comment.get("hidden") else ""
        rows.append(f"<li>Пользователь №{author}: «{content}»{hidden}</li>")
    if len(value) > 8:
        rows.append(f"<li>И ещё комментариев: {len(value) - 8}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_lifecycle(value) -> str:
    if not value:
        return "состояние жизненного цикла не указано"
    current = format_scalar(value.get("current_stage_id") or "не выбран")
    stages = value.get("stages") or []
    rows = [f"<li><strong>Текущий этап:</strong> {current}</li>"]
    for stage in stages[:10]:
        if not isinstance(stage, dict):
            rows.append(f"<li>{format_scalar(stage)}</li>")
            continue
        stage_id = format_scalar(stage.get("id") or "без названия")
        status = format_scalar(stage.get("status"), "status")
        rows.append(f"<li>Этап «{stage_id}»: {status}</li>")
    if len(stages) > 10:
        rows.append(f"<li>И ещё этапов: {len(stages) - 10}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_required_roles(value) -> str:
    if not value:
        return "дополнительные роли не требуются"
    rows = [
        f"<li><strong>{escape(readable_role(role))}:</strong> требуется {format_scalar(count)}</li>"
        for role, count in value.items()
    ]
    return f"<ul>{''.join(rows)}</ul>"


def format_join_requests(value) -> str:
    if not value:
        return "активных заявок нет"
    rows = []
    for request in value[:10]:
        if not isinstance(request, dict):
            rows.append(f"<li>{format_scalar(request)}</li>")
            continue
        user_id = format_scalar(request.get("user_id"))
        role = format_scalar(request.get("requested_role"), "requested_role")
        status = format_scalar(request.get("status"), "status")
        rows.append(f"<li>Пользователь №{user_id}, роль: {role}, статус: {status}</li>")
    if len(value) > 10:
        rows.append(f"<li>И ещё заявок: {len(value) - 10}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


def format_suggestions(value) -> str:
    if not value:
        return "предложений нет"
    rows = []
    for suggestion in value[:8]:
        if not isinstance(suggestion, dict):
            rows.append(f"<li>{format_scalar(suggestion)}</li>")
            continue
        author = format_scalar(suggestion.get("author_id"))
        target = format_scalar(suggestion.get("target_type"))
        status = format_scalar(suggestion.get("status"), "status")
        changes = format_generic_value(suggestion.get("changes") or {})
        rows.append(
            f"<li>Автор №{author}, объект: {target}, статус: {status}. "
            f"<strong>Предлагается:</strong> {changes}</li>"
        )
    if len(value) > 8:
        rows.append(f"<li>И ещё предложений: {len(value) - 8}.</li>")
    return f"<ul>{''.join(rows)}</ul>"


FIELD_FORMATTERS = {
    "participants": format_participants,
    "tasks": format_tasks,
    "links": format_links,
    "comments": format_comments,
    "lifecycle_state": format_lifecycle,
    "required_roles": format_required_roles,
    "join_requests": format_join_requests,
    "suggestions": format_suggestions,
}


def format_project_change_details(diff: dict) -> str:
    """Формирует краткий и безопасный список конкретных изменений."""
    if not diff:
        return "<li>Дополнительные сведения отсутствуют.</li>"

    details = []
    for field, value in list(diff.items())[:8]:
        label = escape(PROJECT_FIELD_LABELS.get(field, field.replace("_", " ")))
        formatter = FIELD_FORMATTERS.get(field)
        rendered_value = formatter(value) if formatter else format_generic_value(value, field)
        details.append(f"<li><strong>{label}:</strong> {rendered_value}</li>")

    if len(diff) > 8:
        details.append(f"<li>И ещё изменено полей: {len(diff) - 8}.</li>")
    return "".join(details)

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
    diff: dict,
):
    """Отправляет подробное уведомление о значимом изменении проекта."""
    safe_project = escape(project_title)
    safe_actor = escape(actor_name)
    safe_description = escape(PROJECT_CHANGE_LABELS.get(change_type, change_type.replace("_", " ")))
    change_details = format_project_change_details(diff)
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
      <p><strong>Подробности изменения:</strong></p>
      <ul>{change_details}</ul>
      <p style="color: #666;">Сложность изменения: {points} очков.</p>
      <p style="color: #777; font-size: 13px;">
        Уведомления о значимых изменениях можно выключить или снова включить в вашем профиле LSP.
      </p>
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
