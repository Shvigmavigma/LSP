from io import BytesIO
from pathlib import Path
import re
from typing import Any, Dict, List

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill


IMPORT_SPECS: Dict[str, Dict[str, Any]] = {
    "student_emails": {"columns": ["email"], "example": ["student@lit1533.ru"]},
    "teacher_emails": {"columns": ["email"], "example": ["teacher@example.ru"]},
    "students": {
        "columns": ["fullname", "email", "password", "class"],
        "example": ["Иванов Иван Иванович", "student@lit1533.ru", "StrongPassword123", 10.1],
    },
    "teachers": {
        "columns": ["fullname", "email", "password"],
        "example": ["Петров Петр Петрович", "teacher@example.ru", "StrongPassword123"],
    },
    "projects": {
        "columns": ["title", "body", "customer_email"],
        "example": ["Школьный проект", "Краткое описание проекта", "customer@example.ru"],
    },
}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CUSTOM_TEMPLATES_DIR = Path("excel_templates")


class ExcelImportValidationError(ValueError):
    pass


def create_excel_template(import_type: str) -> BytesIO:
    spec = IMPORT_SPECS.get(import_type)
    if not spec:
        raise ExcelImportValidationError("Неизвестный тип импорта")

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "import"
    worksheet.append(spec["columns"])
    worksheet.append(spec["example"])
    for cell in worksheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F855A")
    for index, column in enumerate(spec["columns"], start=1):
        sample = str(spec["example"][index - 1])
        worksheet.column_dimensions[worksheet.cell(1, index).column_letter].width = max(
            len(column) + 4, len(sample) + 4
        )

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


def get_excel_template(import_type: str) -> BytesIO:
    if import_type not in IMPORT_SPECS:
        raise ExcelImportValidationError("Неизвестный тип импорта")
    custom_template = CUSTOM_TEMPLATES_DIR / f"{import_type}.xlsx"
    if custom_template.exists():
        return BytesIO(custom_template.read_bytes())
    return create_excel_template(import_type)


def install_excel_template(content: bytes, import_type: str) -> None:
    # A custom template may contain examples and formatting, but its required
    # header must remain identical to the system format.
    parse_excel_headers(content, import_type)
    CUSTOM_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    (CUSTOM_TEMPLATES_DIR / f"{import_type}.xlsx").write_bytes(content)


def reset_excel_template(import_type: str) -> bool:
    if import_type not in IMPORT_SPECS:
        raise ExcelImportValidationError("Неизвестный тип импорта")
    custom_template = CUSTOM_TEMPLATES_DIR / f"{import_type}.xlsx"
    if custom_template.exists():
        custom_template.unlink()
        return True
    return False


def parse_excel_headers(content: bytes, import_type: str) -> None:
    spec = IMPORT_SPECS.get(import_type)
    if not spec:
        raise ExcelImportValidationError("Неизвестный тип импорта")
    if not content:
        raise ExcelImportValidationError("Файл пуст")
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise ExcelImportValidationError("Не удалось прочитать XLSX-файл") from exc
    if len(workbook.sheetnames) != 1:
        raise ExcelImportValidationError("В файле должен быть ровно один лист")
    worksheet = workbook[workbook.sheetnames[0]]
    first_row = next(worksheet.iter_rows(values_only=True), None)
    if not first_row:
        raise ExcelImportValidationError("В файле отсутствует строка заголовков")
    headers = [str(value).strip() if value is not None else "" for value in first_row]
    expected = spec["columns"]
    if headers != expected:
        raise ExcelImportValidationError(
            f"Колонки должны строго соответствовать шаблону: {', '.join(expected)}"
        )


def parse_excel_import(content: bytes, import_type: str) -> List[Dict[str, Any]]:
    spec = IMPORT_SPECS.get(import_type)
    if not spec:
        raise ExcelImportValidationError("Неизвестный тип импорта")
    parse_excel_headers(content, import_type)
    try:
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise ExcelImportValidationError("Не удалось прочитать XLSX-файл") from exc
    rows = list(workbook[workbook.sheetnames[0]].iter_rows(values_only=True))
    expected = spec["columns"]

    parsed: List[Dict[str, Any]] = []
    seen_emails = set()
    for excel_row, values in enumerate(rows[1:], start=2):
        if all(value is None or str(value).strip() == "" for value in values):
            continue
        if len(values) != len(expected):
            raise ExcelImportValidationError(f"Строка {excel_row}: неверное количество колонок")
        item = {
            column: value.strip() if isinstance(value, str) else value
            for column, value in zip(expected, values)
        }
        missing = [
            column for column in expected
            if item[column] is None or str(item[column]).strip() == ""
        ]
        if missing:
            raise ExcelImportValidationError(
                f"Строка {excel_row}: не заполнены обязательные поля: {', '.join(missing)}"
            )
        email_field = "customer_email" if import_type == "projects" else "email"
        email = str(item[email_field]).strip().lower()
        if not EMAIL_PATTERN.fullmatch(email):
            raise ExcelImportValidationError(f"Строка {excel_row}: некорректная почта")
        if import_type != "projects" and email in seen_emails:
            raise ExcelImportValidationError(f"Строка {excel_row}: почта повторяется в файле")
        seen_emails.add(email)
        item[email_field] = email
        if import_type == "students":
            try:
                item["class"] = float(item["class"])
            except (TypeError, ValueError) as exc:
                raise ExcelImportValidationError(
                    f"Строка {excel_row}: класс должен быть числом, например 10.1"
                ) from exc
        item["_row"] = excel_row
        parsed.append(item)
    if not parsed:
        raise ExcelImportValidationError("После заголовка нет данных для импорта")
    return parsed
