from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Iterable

from sqlalchemy.orm import Session

from backend.app.models import Category, Employee, MonthlySalary, MonthlySetting, Project, TimesheetEntry


ZERO = Decimal("0")
HUNDRED = Decimal("100")
MONEY_QUANTUM = Decimal("0.01")
MONTH_LOOKUP = {
	"jan": 1,
	"january": 1,
	"feb": 2,
	"february": 2,
	"mar": 3,
	"march": 3,
	"apr": 4,
	"april": 4,
	"may": 5,
	"jun": 6,
	"june": 6,
	"jul": 7,
	"july": 7,
	"aug": 8,
	"august": 8,
	"sep": 9,
	"sept": 9,
	"september": 9,
	"oct": 10,
	"october": 10,
	"nov": 11,
	"november": 11,
	"dec": 12,
	"december": 12,
}


def _decimal(value: object | None) -> Decimal:
	return ZERO if value is None else Decimal(str(value))


def _money(value: Decimal | None) -> Decimal | None:
	return None if value is None else value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _period_filter(query, model, year: int | None, month: int | None):
	if year is not None:
		query = query.filter(model.year == year)
	if month is not None:
		query = query.filter(model.month == month)
	return query


def _billable_categories(session: Session, dataset_id: int) -> set[str]:
	return {row.name for row in session.query(Category).filter(Category.dataset_id == dataset_id, Category.is_billable.is_(True))}


def _entries(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> list[TimesheetEntry]:
	return _period_filter(session.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset_id), TimesheetEntry, year, month).all()


def _sales_period(value: str | None) -> tuple[int | None, int | None]:
	if not value:
		return (None, None)
	normalized = value.strip().lower().replace("'", " ")
	parts = re.findall(r"[a-z]+|\d+", normalized)
	sale_month = next((MONTH_LOOKUP[part] for part in parts if part in MONTH_LOOKUP), None)
	year_numbers = [int(part) for part in parts if part.isdigit()]
	sale_year = None
	if year_numbers:
		sale_year = year_numbers[-1]
		if sale_year < 100:
			sale_year += 2000
	return (sale_year, sale_month)


def _project_revenue_matches_period(project: Project, year: int | None, month: int | None) -> bool:
	if month is None:
		return True
	sale_year, sale_month = _sales_period(project.sales_month)
	if sale_month is None:
		return False
	if sale_month != month:
		return False
	return year is None or sale_year is None or sale_year == year


@dataclass
class EmployeeMonthlyRate:
	employee_no: str
	employee_name: str
	year: int
	month: int
	salary: Decimal
	total_hours: Decimal
	billable_hours: Decimal
	non_billable_hours: Decimal
	direct_rate: Decimal
	productivity: Decimal


@dataclass
class ProjectProfitability:
	ref_code: str
	project_name: str | None
	project_price: Decimal | None
	total_hours: Decimal
	total_cost: Decimal
	profit: Decimal | None
	margin: Decimal | None
	status: str


@dataclass
class EmployeeProjectProfitability:
	employee_no: str
	employee_name: str
	ref_code: str
	project_hours: Decimal
	direct_rate: Decimal
	revenue_share: Decimal | None
	employee_cost: Decimal
	profitability: Decimal | None


@dataclass
class CategorySummary:
	category: str
	total_hours: Decimal
	percentage: Decimal
	is_billable: bool


@dataclass
class CompanySummary:
	total_hours: Decimal
	billable_hours: Decimal
	non_billable_hours: Decimal
	total_salary: Decimal
	total_revenue: Decimal
	total_cost: Decimal
	profit: Decimal | None
	margin: Decimal | None
	overhead: Decimal
	indirect_pool: Decimal
	calculated_company_cost: Decimal
	unallocated_cost: Decimal
	productivity: Decimal


def calculate_direct_rate(salary: Decimal | int | float, total_hours: Decimal | int | float) -> Decimal:
	hours = _decimal(total_hours)
	return ZERO if hours == ZERO else _decimal(salary) / hours


def calculate_non_billable_cost_value(non_billable_hours: Decimal | int | float, direct_rate: Decimal | int | float) -> Decimal:
	return _decimal(non_billable_hours) * _decimal(direct_rate)


def calculate_indirect_rate_value(indirect_pool: Decimal | int | float, billable_hours: Decimal | int | float) -> Decimal:
	hours = _decimal(billable_hours)
	return ZERO if hours == ZERO else _decimal(indirect_pool) / hours


def calculate_project_employee_cost_value(hours: Decimal | int | float, direct_rate: Decimal | int | float, indirect_rate: Decimal | int | float) -> Decimal:
	return _decimal(hours) * (_decimal(direct_rate) + _decimal(indirect_rate))


def calculate_project_profit_value(revenue: Decimal | int | float | None, cost: Decimal | int | float) -> Decimal | None:
	return None if revenue is None else _decimal(revenue) - _decimal(cost)


def calculate_project_margin_value(profit: Decimal | int | float | None, revenue: Decimal | int | float | None) -> Decimal | None:
	return None if revenue in (None, ZERO, 0) else _decimal(profit) / _decimal(revenue) * HUNDRED


def calculate_total_hours(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	return sum((_decimal(entry.hours) for entry in _entries(session, dataset_id, year, month)), ZERO)


def calculate_billable_hours(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	billable = _billable_categories(session, dataset_id)
	return sum((_decimal(entry.hours) for entry in _entries(session, dataset_id, year, month) if entry.category in billable), ZERO)


def calculate_non_billable_hours(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	return calculate_total_hours(session, dataset_id, year, month) - calculate_billable_hours(session, dataset_id, year, month)


def calculate_employee_monthly_rates(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> list[EmployeeMonthlyRate]:
	entries = _entries(session, dataset_id, year, month)
	billable = _billable_categories(session, dataset_id)
	hours: dict[tuple[int, int, int], Decimal] = defaultdict(lambda: ZERO)
	billable_hours: dict[tuple[int, int, int], Decimal] = defaultdict(lambda: ZERO)
	for entry in entries:
		key = (entry.employee_id, entry.year, entry.month)
		hours[key] += _decimal(entry.hours)
		if entry.category in billable:
			billable_hours[key] += _decimal(entry.hours)
	salaries = _period_filter(session.query(MonthlySalary).filter(MonthlySalary.dataset_id == dataset_id), MonthlySalary, year, month).all()
	salary_by_key = {(row.employee_id, row.year, row.month): _decimal(row.salary) for row in salaries}
	employees = {employee.id: employee for employee in session.query(Employee).filter(Employee.dataset_id == dataset_id).all()}
	keys = set(hours) | set(salary_by_key)
	return [
		EmployeeMonthlyRate(
			employee_no=employees[employee_id].employee_no,
			employee_name=employees[employee_id].employee_name,
			year=entry_year,
			month=entry_month,
			salary=salary_by_key.get((employee_id, entry_year, entry_month), ZERO),
			total_hours=hours.get((employee_id, entry_year, entry_month), ZERO),
			billable_hours=billable_hours.get((employee_id, entry_year, entry_month), ZERO),
			non_billable_hours=hours.get((employee_id, entry_year, entry_month), ZERO) - billable_hours.get((employee_id, entry_year, entry_month), ZERO),
			direct_rate=calculate_direct_rate(salary_by_key.get((employee_id, entry_year, entry_month), ZERO), hours.get((employee_id, entry_year, entry_month), ZERO)),
			productivity=ZERO if hours.get((employee_id, entry_year, entry_month), ZERO) == ZERO else billable_hours.get((employee_id, entry_year, entry_month), ZERO) / hours[(employee_id, entry_year, entry_month)] * HUNDRED,
		)
		for employee_id, entry_year, entry_month in sorted(keys)
	]


def calculate_non_billable_cost(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	return sum((calculate_non_billable_cost_value(row.non_billable_hours, row.direct_rate) for row in calculate_employee_monthly_rates(session, dataset_id, year, month)), ZERO)


def calculate_zero_hour_salary(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	return sum((row.salary for row in calculate_employee_monthly_rates(session, dataset_id, year, month) if row.total_hours == ZERO), ZERO)


def calculate_indirect_pool(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	settings = _period_filter(session.query(MonthlySetting).filter(MonthlySetting.dataset_id == dataset_id), MonthlySetting, year, month).all()
	overhead = sum((_decimal(setting.overhead) for setting in settings), ZERO)
	return calculate_zero_hour_salary(session, dataset_id, year, month) + calculate_non_billable_cost(session, dataset_id, year, month) + overhead


def calculate_indirect_rate(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	return calculate_indirect_rate_value(calculate_indirect_pool(session, dataset_id, year, month), calculate_billable_hours(session, dataset_id, year, month))


def _project_rates(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> dict[tuple[int, int, int], EmployeeMonthlyRate]:
	return {(row.employee_no, row.year, row.month): row for row in calculate_employee_monthly_rates(session, dataset_id, year, month)}


def calculate_project_employee_cost(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> list[EmployeeProjectProfitability]:
	entries = _entries(session, dataset_id, year, month)
	billable = _billable_categories(session, dataset_id)
	rates = {(row.employee_no, row.year, row.month): row for row in calculate_employee_monthly_rates(session, dataset_id, year, month)}
	indirect_rates = {
		(period_year, period_month): calculate_indirect_rate(session, dataset_id, period_year, period_month)
		for period_year, period_month in {(entry.year, entry.month) for entry in entries}
	}
	grouped: dict[tuple[int, int, int, int], Decimal] = defaultdict(lambda: ZERO)
	names: dict[int, tuple[str, str]] = {}
	for entry in entries:
		if entry.project_id is None or entry.category not in billable:
			continue
		key = (entry.employee_id, entry.project_id, entry.year, entry.month)
		grouped[key] += _decimal(entry.hours)
		names[entry.employee_id] = (entry.employee.employee_no, entry.employee.employee_name)
	project_hours: dict[int, Decimal] = defaultdict(lambda: ZERO)
	for (_, project_id, _, _), hours in grouped.items():
		project_hours[project_id] += hours
	projects = {project.id: project for project in session.query(Project).filter(Project.dataset_id == dataset_id).all()}
	employee_month_hours: dict[tuple[str, int, int], Decimal] = {}
	for rate in rates.values():
		employee_month_hours[(rate.employee_no, rate.year, rate.month)] = rate.direct_rate
	result = []
	for (employee_id, project_id, entry_year, entry_month), hours in grouped.items():
		project = projects[project_id]
		employee_no, employee_name = names[employee_id]
		direct_rate = employee_month_hours.get((employee_no, entry_year, entry_month), ZERO)
		revenue_share = None if project.project_price is None else _decimal(project.project_price) * hours / project_hours[project_id]
		cost = calculate_project_employee_cost_value(hours, direct_rate, indirect_rates[(entry_year, entry_month)])
		profitability = None if revenue_share in (None, ZERO) else (revenue_share - cost) / revenue_share * HUNDRED
		result.append(EmployeeProjectProfitability(employee_no, employee_name, project.ref_code, hours, direct_rate, revenue_share, cost, profitability))
	return result


def calculate_project_summary(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> list[ProjectProfitability]:
	costs: dict[str, Decimal] = defaultdict(lambda: ZERO)
	hours: dict[str, Decimal] = defaultdict(lambda: ZERO)
	for row in calculate_project_employee_cost(session, dataset_id, year, month):
		costs[row.ref_code] += row.employee_cost
		hours[row.ref_code] += row.project_hours
	projects = session.query(Project).filter(Project.dataset_id == dataset_id).all()
	return [
		ProjectProfitability(project.ref_code, project.project_name, _decimal(project.project_price) if project.project_price is not None else None, hours[project.ref_code], costs[project.ref_code], calculate_project_profit_value(project.project_price, costs[project.ref_code]), calculate_project_margin_value(calculate_project_profit_value(project.project_price, costs[project.ref_code]), project.project_price), "unpriced" if project.project_price is None else ("loss" if costs[project.ref_code] > _decimal(project.project_price) else "profitable"))
		for project in projects
	]


def calculate_employee_revenue_share(project_revenue: Decimal | int | float | None, employee_project_hours: Decimal | int | float, total_project_hours: Decimal | int | float) -> Decimal | None:
	total = _decimal(total_project_hours)
	return None if project_revenue is None or total == ZERO else _decimal(project_revenue) * _decimal(employee_project_hours) / total


def calculate_employee_profitability(revenue_share: Decimal | int | float | None, employee_cost: Decimal | int | float) -> Decimal | None:
	share = _decimal(revenue_share) if revenue_share is not None else ZERO
	return None if share == ZERO else (share - _decimal(employee_cost)) / share * HUNDRED


def calculate_productivity(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> Decimal:
	total = calculate_total_hours(session, dataset_id, year, month)
	return ZERO if total == ZERO else calculate_billable_hours(session, dataset_id, year, month) / total * HUNDRED


def calculate_category_summary(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> list[CategorySummary]:
	totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
	for entry in _entries(session, dataset_id, year, month):
		totals[entry.category] += _decimal(entry.hours)
	total = sum(totals.values(), ZERO)
	billable = _billable_categories(session, dataset_id)
	return [CategorySummary(category, hours, ZERO if total == ZERO else hours / total * HUNDRED, category in billable) for category, hours in sorted(totals.items())]


def calculate_company_summary(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> CompanySummary:
	all_projects = session.query(Project).filter(Project.dataset_id == dataset_id).all()
	rates = calculate_employee_monthly_rates(session, dataset_id, year, month)
	total_salary = sum((row.salary for row in rates), ZERO)
	overhead = sum((_decimal(row.overhead) for row in _period_filter(session.query(MonthlySetting).filter(MonthlySetting.dataset_id == dataset_id), MonthlySetting, year, month).all()), ZERO)
	direct_logged_cost = sum((row.direct_rate * row.total_hours for row in rates), ZERO)
	zero_hour_salary = sum((row.salary for row in rates if row.total_hours == ZERO), ZERO)
	total_cost = direct_logged_cost + zero_hour_salary + overhead
	revenue = sum(
		(
			_decimal(project.project_price)
			for project in all_projects
			if project.project_price is not None and _project_revenue_matches_period(project, year, month)
		),
		ZERO,
	)
	profit = revenue - total_cost
	return CompanySummary(calculate_total_hours(session, dataset_id, year, month), calculate_billable_hours(session, dataset_id, year, month), calculate_non_billable_hours(session, dataset_id, year, month), total_salary, revenue, total_cost, profit, None if revenue == ZERO else profit / revenue * HUNDRED, overhead, calculate_indirect_pool(session, dataset_id, year, month), total_cost, ZERO, calculate_productivity(session, dataset_id, year, month))


def reconcile_company_cost(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> dict[str, object]:
	summary = calculate_company_summary(session, dataset_id, year, month)
	difference = summary.calculated_company_cost - summary.total_salary
	return {"total_salary": _money(summary.total_salary), "calculated_company_cost": _money(summary.calculated_company_cost), "difference": _money(difference), "passed": abs(difference) <= MONEY_QUANTUM}


def reconcile_project_costs(session: Session, dataset_id: int, year: int | None = None, month: int | None = None) -> dict[str, Decimal | bool]:
	allocated = sum((row.total_cost for row in calculate_project_summary(session, dataset_id, year, month)), ZERO)
	entries = _entries(session, dataset_id, year, month)
	billable = _billable_categories(session, dataset_id)
	rates = {(row.employee_no, row.year, row.month): row.direct_rate for row in calculate_employee_monthly_rates(session, dataset_id, year, month)}
	indirect_rates = {(entry.year, entry.month): calculate_indirect_rate(session, dataset_id, entry.year, entry.month) for entry in entries}
	unallocated = sum(
		(calculate_project_employee_cost_value(entry.hours, rates.get((entry.employee.employee_no, entry.year, entry.month), ZERO), indirect_rates[(entry.year, entry.month)]) for entry in entries if entry.category in billable and entry.project_id is None),
		ZERO,
	)
	expected = calculate_company_summary(session, dataset_id, year, month).calculated_company_cost
	difference = allocated + unallocated - expected
	return {"allocated_project_cost": _money(allocated), "unallocated_cost": _money(unallocated), "calculated_company_cost": _money(expected), "difference": _money(difference), "passed": abs(difference) <= MONEY_QUANTUM}
