from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    timesheet_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    salary_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    project_filename: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employees: Mapped[list["Employee"]] = relationship(back_populates="dataset")
    monthly_salaries: Mapped[list["MonthlySalary"]] = relationship(back_populates="dataset")
    projects: Mapped[list["Project"]] = relationship(back_populates="dataset")
    timesheet_entries: Mapped[list["TimesheetEntry"]] = relationship(back_populates="dataset")
    categories: Mapped[list["Category"]] = relationship(back_populates="dataset")
    monthly_settings: Mapped[list["MonthlySetting"]] = relationship(back_populates="dataset")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("dataset_id", "employee_no", name="uq_employees_dataset_employee_no"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    employee_no: Mapped[str] = mapped_column(String, nullable=False)
    employee_name: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    designation: Mapped[str | None] = mapped_column(String, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="employees")
    monthly_salaries: Mapped[list["MonthlySalary"]] = relationship(back_populates="employee")
    timesheet_entries: Mapped[list["TimesheetEntry"]] = relationship(back_populates="employee")


class MonthlySalary(Base):
    __tablename__ = "monthly_salaries"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "employee_id",
            "year",
            "month",
            name="uq_monthly_salaries_dataset_employee_month",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="monthly_salaries")
    employee: Mapped["Employee"] = relationship(back_populates="monthly_salaries")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("dataset_id", "ref_code", name="uq_projects_dataset_ref_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    ref_code: Mapped[str] = mapped_column(String, nullable=False)
    project_name: Mapped[str | None] = mapped_column(String, nullable=True)
    project_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    sales_month: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="projects")
    timesheet_entries: Mapped[list["TimesheetEntry"]] = relationship(back_populates="project")


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    task_name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="timesheet_entries")
    employee: Mapped["Employee"] = relationship(back_populates="timesheet_entries")
    project: Mapped["Project | None"] = relationship(back_populates="timesheet_entries")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("dataset_id", "name", name="uq_categories_dataset_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_billable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="categories")


class MonthlySetting(Base):
    __tablename__ = "monthly_settings"
    __table_args__ = (
        UniqueConstraint("dataset_id", "year", "month", name="uq_monthly_settings_dataset_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    overhead: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    dataset: Mapped["Dataset"] = relationship(back_populates="monthly_settings")
