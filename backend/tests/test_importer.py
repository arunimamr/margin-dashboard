from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from backend.app.database import init_db
from backend.app.models import Dataset, Employee, MonthlySalary, Project, TimesheetEntry
from backend.app.services.data_quality import ImportValidationError
from backend.app.services.importer import (
    import_dataset,
    load_project_excel,
    load_salary_excel,
    load_timesheet_excel,
    normalize_column_name,
)


ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "sample-data"


def database(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'import.db').as_posix()}")
    init_db(engine)
    return engine


def paths():
    return (SAMPLE / "timesheet-2025.xlsx", SAMPLE / "salaries-2025.xlsx", SAMPLE / "project-prices-2025.xlsx")


def test_excel_files_load_and_headers_are_normalized():
    timesheet_path, salary_path, project_path = paths()
    timesheet = load_timesheet_excel(timesheet_path)
    salary = load_salary_excel(salary_path)
    projects = load_project_excel(project_path)
    assert normalize_column_name(" Employee No. ") == "employee no"
    assert {"employee_no", "task_name", "hours"}.issubset(timesheet.columns)
    assert {"employee_no", "January", "December"}.issubset(salary.columns)
    assert {"ref_code", "project_name", "project_price"}.issubset(projects.columns)


def test_import_normalizes_salary_months_and_deduplicates_employees(tmp_path):
    engine = database(tmp_path)
    result = import_dataset(*paths(), "Sample", session=Session(engine))
    with Session(engine) as session:
        assert result["employees_imported"] == 14
        assert session.query(Employee).filter(Employee.dataset_id == result["dataset_id"]).count() == 14
        assert session.query(MonthlySalary).filter(MonthlySalary.dataset_id == result["dataset_id"]).count() == 144
        assert session.query(MonthlySalary.month).filter(MonthlySalary.dataset_id == result["dataset_id"], MonthlySalary.month == 1).count() == 12


def test_missing_project_price_keeps_timesheet_row_without_project(tmp_path):
    engine = database(tmp_path)
    result = import_dataset(*paths(), "Sample", session=Session(engine))
    with Session(engine) as session:
        entries = session.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == result["dataset_id"]).all()
        assert len(entries) == 562
        assert any(entry.project_id is None for entry in entries)
        assert any("has no project" in warning for warning in result["warnings"])
        assert any("has no salary" in warning for warning in result["warnings"])


def test_dataset_isolation_and_duplicate_name_rejection(tmp_path):
    engine = database(tmp_path)
    first = import_dataset(*paths(), "First", session=Session(engine))
    second = import_dataset(*paths(), "Second", session=Session(engine))
    with Session(engine) as session:
        assert session.query(Dataset).count() == 2
        assert session.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == first["dataset_id"]).count() == 562
        assert session.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == second["dataset_id"]).count() == 562
    with pytest.raises(ImportValidationError, match="already exists"):
        import_dataset(*paths(), "First", session=Session(engine))


def test_failed_import_rolls_back_dataset(tmp_path):
    engine = database(tmp_path)
    with pytest.raises(ImportValidationError, match="must contain a 'Projects' sheet"):
        import_dataset(paths()[0], paths()[1], paths()[0], "Broken", session=Session(engine))
    with Session(engine) as session:
        assert session.query(func.count(Dataset.id)).scalar() == 0