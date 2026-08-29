from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.database import init_db
from backend.app.services.calculations import (
	calculate_direct_rate,
	calculate_employee_profitability,
	calculate_employee_revenue_share,
	calculate_company_summary,
	calculate_indirect_rate_value,
	calculate_non_billable_cost_value,
	calculate_project_employee_cost_value,
	calculate_project_margin_value,
	calculate_project_profit_value,
	reconcile_company_cost,
)
from backend.app.services.importer import import_dataset


def test_calculation_formulas():
	assert calculate_direct_rate(10000, 200) == Decimal("50")
	assert calculate_direct_rate(10000, 0) == Decimal("0")
	assert calculate_non_billable_cost_value(20, 50) == Decimal("1000")
	assert calculate_indirect_rate_value(10000, 500) == Decimal("20")
	assert calculate_project_employee_cost_value(100, 50, 20) == Decimal("7000")
	assert calculate_project_profit_value(100000, 70000) == Decimal("30000")
	assert calculate_project_margin_value(30000, 100000) == Decimal("30")
	assert calculate_project_profit_value(100000, 120000) == Decimal("-20000")
	assert calculate_project_margin_value(-20000, 100000) == Decimal("-20")
	assert calculate_employee_revenue_share(100000, 200, 1000) == Decimal("20000")
	assert calculate_employee_profitability(20000, 14000) == Decimal("30")


def test_zero_denominators_return_safe_values():
	assert calculate_indirect_rate_value(10000, 0) == Decimal("0")
	assert calculate_project_margin_value(100, 0) is None
	assert calculate_employee_revenue_share(100, 10, 0) is None
	assert calculate_employee_profitability(0, 100) is None


def test_real_sample_zero_overhead_reconciles(tmp_path):
	root = Path(__file__).resolve().parents[2]
	engine = create_engine(f"sqlite:///{(tmp_path / 'calculation.db').as_posix()}")
	init_db(engine)
	with Session(engine) as session:
		result = import_dataset(root / "sample-data/timesheet-2025.xlsx", root / "sample-data/salaries-2025.xlsx", root / "sample-data/project-prices-2025.xlsx", "2025 Sample", session=session)
		reconciliation = reconcile_company_cost(session, result["dataset_id"])
		assert reconciliation["passed"] is True
		assert reconciliation["difference"] == Decimal("0.00")


def test_monthly_company_revenue_uses_project_sales_month(tmp_path):
	root = Path(__file__).resolve().parents[2]
	engine = create_engine(f"sqlite:///{(tmp_path / 'calculation.db').as_posix()}")
	init_db(engine)
	with Session(engine) as session:
		result = import_dataset(root / "sample-data/timesheet-2025.xlsx", root / "sample-data/salaries-2025.xlsx", root / "sample-data/project-prices-2025.xlsx", "2025 Sample", session=session)
		full_year = calculate_company_summary(session, result["dataset_id"], 2025)
		january = calculate_company_summary(session, result["dataset_id"], 2025, 1)
		june = calculate_company_summary(session, result["dataset_id"], 2025, 6)

		assert full_year.total_revenue == Decimal("5012000")
		assert january.total_revenue == Decimal("560000")
		assert june.total_revenue == Decimal("980000")
