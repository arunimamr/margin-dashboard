import re
from calendar import month_name
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Category, Dataset, Employee, MonthlySalary, MonthlySetting, Project, TimesheetEntry
from backend.app.services.data_quality import DataQualityReport, ImportValidationError, validate_required_columns


TIMESHEET_COLUMN_MAP = {
    "month": "month", "employee no": "employee_no", "employee name": "employee_name",
    "type of expense": "type_of_expense", "department": "department", "designation": "designation",
    "category": "category", "ref code": "ref_code", "project billable task unbillable name": "task_name",
    "company name billable fixed costs unbillable": "cost_context", "description": "description", "hours": "hours",
}
SALARY_COLUMN_MAP = {"employee no": "employee_no", "employee name": "employee_name"}
PROJECT_COLUMN_MAP = {
    "ref code": "ref_code", "project billable name": "project_name", "project price": "project_price",
    "sales month": "sales_month", "category": "category", "status": "status",
}
MONTHS = {month.lower(): number for number, month in enumerate(month_name) if month}
DEFAULT_BILLABLE_CATEGORIES = {"Projects", "Enhancements", "Hosting"}


def normalize_column_name(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower())
    return re.sub(r"\s+", " ", text).strip()


def _normalize_frame(frame: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    renamed = {column: mapping[normalize_column_name(column)] for column in frame.columns if normalize_column_name(column) in mapping}
    result = frame.rename(columns=renamed).copy()
    for column in result.columns:
        if result[column].dtype == object:
            result[column] = result[column].map(lambda value: value.strip() if isinstance(value, str) else value)
    return result


def _require_sheet(path: str | Path, expected: str) -> pd.DataFrame:
    workbook = pd.ExcelFile(path)
    if expected not in workbook.sheet_names:
        raise ImportValidationError(f"{path} must contain a '{expected}' sheet")
    return pd.read_excel(path, sheet_name=expected)


def load_timesheet_excel(path: str | Path) -> pd.DataFrame:
    return _normalize_frame(_require_sheet(path, "Timesheet"), TIMESHEET_COLUMN_MAP)


def load_salary_excel(path: str | Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Salary", header=None)
    header_index = next((index for index, row in raw.iterrows() if any(normalize_column_name(value) == "employee no" for value in row)), None)
    if header_index is None:
        raise ImportValidationError(f"{path} does not contain an Employee No. header")
    frame = raw.iloc[header_index + 1 :].copy()
    frame.columns = raw.iloc[header_index].tolist()
    return _normalize_frame(frame, SALARY_COLUMN_MAP)


def load_project_excel(path: str | Path) -> pd.DataFrame:
    return _normalize_frame(_require_sheet(path, "Projects"), PROJECT_COLUMN_MAP)


def _text(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _employee_no(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith(".0"):
        text = text[:-2]
    if re.fullmatch(r"\d+", text) and len(text) < 5:
        return text.zfill(5)
    return text


def _decimal(value: object) -> Decimal | None:
    if value is None or pd.isna(value) or (isinstance(value, str) and not value.strip()):
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _month_year(value: object, default_year: int | None = None) -> tuple[int, int] | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return int(value.year), int(value.month)
    text = str(value).strip().lower()
    for name, number in MONTHS.items():
        if re.search(rf"\b{name}\b", text):
            year_match = re.search(r"(20\d{2})", text)
            if year_match or default_year:
                return int(year_match.group(1)) if year_match else default_year, number
            return None
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else (int(parsed.year), int(parsed.month))


def _infer_year(frame: pd.DataFrame, path: str | Path) -> int:
    for value in frame.get("month", []):
        parsed = _month_year(value)
        if parsed:
            return parsed[0]
    match = re.search(r"20\d{2}", Path(path).stem)
    if match:
        return int(match.group())
    raise ImportValidationError("Could not determine the dataset year from the timesheet")


def _check_columns(frame: pd.DataFrame, required: Iterable[str], source: str) -> None:
    report = DataQualityReport()
    validate_required_columns(frame, set(required), source, report)
    if report.errors:
        raise ImportValidationError(report.errors[0], report)


def import_dataset(timesheet_path: str | Path, salary_path: str | Path, project_path: str | Path, dataset_name: str, session: Session | None = None) -> dict[str, object]:
    timesheet = load_timesheet_excel(timesheet_path)
    salary = load_salary_excel(salary_path)
    projects = load_project_excel(project_path)
    _check_columns(timesheet, {"month", "employee_no", "employee_name", "department", "designation", "category", "ref_code", "task_name", "description", "hours"}, "Timesheet")
    _check_columns(salary, {"employee_no", "employee_name"}, "Salary")
    _check_columns(projects, {"ref_code", "project_name", "project_price", "sales_month", "category", "status"}, "Projects")
    report = DataQualityReport()
    year = _infer_year(timesheet, timesheet_path)
    owns_session = session is None
    db = session or SessionLocal()
    try:
        if db.query(Dataset).filter(Dataset.name == dataset_name).first():
            raise ImportValidationError(f"Dataset '{dataset_name}' already exists")
        db.query(Dataset).update({Dataset.is_active: False})
        dataset = Dataset(name=dataset_name, timesheet_filename=Path(timesheet_path).name, salary_filename=Path(salary_path).name, project_filename=Path(project_path).name, is_active=True)
        db.add(dataset)
        db.flush()
        employee_values: dict[str, dict[str, str | None]] = {}
        for frame in (timesheet, salary):
            for _, row in frame.iterrows():
                number = _employee_no(row.get("employee_no"))
                if number is None:
                    report.warning("Blank employee number skipped")
                    continue
                values = {"employee_name": _text(row.get("employee_name")), "department": _text(row.get("department")), "designation": _text(row.get("designation"))}
                if number in employee_values:
                    for key, value in values.items():
                        if value and employee_values[number].get(key) and value != employee_values[number][key]:
                            report.warning(f"Conflicting {key} for employee {number}")
                else:
                    employee_values[number] = values
        employees: dict[str, Employee] = {}
        for number, values in employee_values.items():
            employee = Employee(dataset=dataset, employee_no=number, employee_name=values["employee_name"] or number, department=values["department"], designation=values["designation"])
            db.add(employee)
            employees[number] = employee
        db.flush()
        project_by_ref: dict[str, Project] = {}
        for _, row in projects.iterrows():
            ref_code = _text(row.get("ref_code"))
            if ref_code is None:
                report.warning("Blank project Ref Code skipped")
                continue
            if ref_code in project_by_ref:
                report.warning(f"Duplicate project Ref Code: {ref_code}; first row used")
                continue
            project = Project(dataset=dataset, ref_code=ref_code, project_name=_text(row.get("project_name")), project_price=_decimal(row.get("project_price")), sales_month=_text(row.get("sales_month")), category=_text(row.get("category")), status=_text(row.get("status")))
            db.add(project)
            project_by_ref[ref_code] = project
        db.flush()
        salary_count = 0
        salary_columns = [(column, MONTHS[normalize_column_name(column)]) for column in salary.columns if normalize_column_name(column) in MONTHS]
        salary_employees: set[str] = set()
        for _, row in salary.iterrows():
            number = _employee_no(row.get("employee_no"))
            if not number or number not in employees:
                continue
            salary_employees.add(number)
            for column, month in salary_columns:
                value = _decimal(row.get(column))
                if value is None:
                    report.warning(f"Missing or invalid salary for employee {number}, month {month}")
                    continue
                db.add(MonthlySalary(dataset=dataset, employee=employees[number], year=year, month=month, salary=value))
                salary_count += 1
        timesheet_count = 0
        category_names: set[str] = set()
        setting_months: set[tuple[int, int]] = set()
        for _, row in timesheet.iterrows():
            number = _employee_no(row.get("employee_no"))
            hours = _decimal(row.get("hours"))
            parsed_month = _month_year(row.get("month"), year)
            if not number or number not in employees:
                report.warning("Timesheet row skipped because employee number is blank or unknown")
                continue
            if hours is None:
                report.warning(f"Invalid or blank hours for employee {number}; row skipped")
                continue
            if parsed_month is None:
                report.warning(f"Invalid month for employee {number}; row skipped")
                continue
            entry_year, entry_month = parsed_month
            category = _text(row.get("category")) or "Uncategorized"
            ref_code = _text(row.get("ref_code"))
            project = project_by_ref.get(ref_code) if ref_code else None
            if ref_code and project is None:
                report.warning(f"Timesheet Ref Code has no project: {ref_code}")
            if number not in salary_employees:
                report.warning(f"Timesheet employee has no salary: {number}")
            db.add(TimesheetEntry(dataset=dataset, employee=employees[number], project=project, year=entry_year, month=entry_month, category=category, department=_text(row.get("department")), hours=hours, task_name=_text(row.get("task_name")), description=_text(row.get("description"))))
            timesheet_count += 1
            category_names.add(category)
            setting_months.add((entry_year, entry_month))
        for _, month in salary_columns:
            setting_months.add((year, month))
        for name in category_names:
            db.add(Category(dataset=dataset, name=name, is_billable=name in DEFAULT_BILLABLE_CATEGORIES))
        for setting_year, setting_month in sorted(setting_months):
            db.add(MonthlySetting(dataset=dataset, year=setting_year, month=setting_month, overhead=Decimal("0")))
        db.commit()
        return {"dataset_id": dataset.id, "status": "success", "employees_imported": len(employees), "salary_records_imported": salary_count, "projects_imported": len(project_by_ref), "timesheet_rows_imported": timesheet_count, "warnings": report.warnings, "errors": report.errors}
    except ImportValidationError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        report.error(str(exc))
        raise ImportValidationError(f"Dataset import failed: {exc}", report) from exc
    finally:
        if owns_session:
            db.close()
