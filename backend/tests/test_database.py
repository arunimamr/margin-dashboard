from decimal import Decimal

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.app.database import Base, init_db
from backend.app.models import Dataset, Employee, MonthlySalary, MonthlySetting, Project, TimesheetEntry


def test_database_schema_and_basic_relationships(tmp_path):
    database_path = tmp_path / "test_margin_dashboard.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    init_db(engine)

    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {
        "datasets",
        "employees",
        "monthly_salaries",
        "projects",
        "timesheet_entries",
        "categories",
        "monthly_settings",
    }

    with Session(engine) as session:
        dataset = Dataset(name="Sample Dataset")
        employee = Employee(
            dataset=dataset,
            employee_no="E001",
            employee_name="Ada Lovelace",
            department="Design",
            designation="Designer",
        )
        project = Project(
            dataset=dataset,
            ref_code="P001",
            project_name="Website Refresh",
            project_price=Decimal("10000.00"),
            sales_month="January",
            category="Projects",
            status="Active",
        )
        salary = MonthlySalary(
            dataset=dataset,
            employee=employee,
            year=2025,
            month=1,
            salary=Decimal("12000.00"),
        )
        timesheet_entry_without_project = TimesheetEntry(
            dataset=dataset,
            employee=employee,
            project_id=None,
            year=2025,
            month=1,
            category="FC - Learning",
            department="Design",
            hours=Decimal("8.00"),
            task_name="Training",
            description="Internal learning time",
        )
        monthly_setting = MonthlySetting(
            dataset=dataset,
            year=2025,
            month=1,
            overhead=Decimal("0.00"),
        )

        session.add_all(
            [
                dataset,
                employee,
                project,
                salary,
                timesheet_entry_without_project,
                monthly_setting,
            ]
        )
        session.commit()

        saved_dataset = session.query(Dataset).one()
        assert saved_dataset.employees == [employee]
        assert saved_dataset.projects == [project]
        assert saved_dataset.monthly_salaries == [salary]
        assert saved_dataset.timesheet_entries == [timesheet_entry_without_project]
        assert saved_dataset.monthly_settings == [monthly_setting]
        assert employee.monthly_salaries == [salary]
        assert employee.timesheet_entries == [timesheet_entry_without_project]
        assert timesheet_entry_without_project.project_id is None

    Base.metadata.drop_all(bind=engine)
