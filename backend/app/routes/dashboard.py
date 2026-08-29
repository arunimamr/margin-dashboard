from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Category, Employee, MonthlySalary, Project, TimesheetEntry
from backend.app.schemas import DashboardResponse, DashboardTrendItem, DashboardTrendResponse, DepartmentAnalyticsItem, DepartmentAnalyticsResponse, PeriodInfo, HoursInfo, FinancialInfo, ReconciliationInfo, SalaryRangeItem
from backend.app.services.calculations import MONEY_QUANTUM, _money, _project_revenue_matches_period, calculate_company_summary
from backend.app.routes.common import selected_dataset, validate_period

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


SALARY_RANGES = [
	("<20k", Decimal("0"), Decimal("20000")),
	("20k-30k", Decimal("20000"), Decimal("30000")),
	("30k-40k", Decimal("30000"), Decimal("40000")),
	("40k-50k", Decimal("40000"), Decimal("50000")),
	("50k-60k", Decimal("50000"), Decimal("60000")),
	("60k-70k", Decimal("60000"), Decimal("70000")),
	("70k-80k", Decimal("70000"), Decimal("80000")),
	("80k-90k", Decimal("80000"), Decimal("90000")),
	("90k-100k", Decimal("90000"), Decimal("100000")),
	(">100k", Decimal("100000"), None),
]


def _period_filter(query, model, year: int | None, month: int | None):
	if year is not None:
		query = query.filter(model.year == year)
	if month is not None:
		query = query.filter(model.month == month)
	return query


def _salary_range(value: Decimal) -> str:
	for label, start, end in SALARY_RANGES:
		if value >= start and (end is None or value < end):
			return label
	return SALARY_RANGES[0][0]


@router.get("", summary="Get company dashboard summary", response_model=DashboardResponse)
def dashboard(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db)
) -> DashboardResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	summary = calculate_company_summary(db, dataset.id, year, month)
	difference = summary.calculated_company_cost - summary.total_salary
	
	return DashboardResponse(
		dataset_id=dataset.id,
		period=PeriodInfo(year=year, month=month),
		hours=HoursInfo(
			total=summary.total_hours,
			billable=summary.billable_hours,
			non_billable=summary.non_billable_hours
		),
		financial=FinancialInfo(
			revenue=summary.total_revenue,
			cost=summary.total_cost,
			profit=summary.profit,
			margin=summary.margin,
			overhead=summary.overhead
		),
		productivity=summary.productivity,
		reconciliation=ReconciliationInfo(
			expected_salary_cost=_money(summary.total_salary),
			calculated_company_cost=_money(summary.calculated_company_cost),
			difference=_money(difference),
			passed=abs(difference) <= MONEY_QUANTUM
		)
	)


@router.get("/trend", summary="Get monthly dashboard trend", response_model=DashboardTrendResponse)
def dashboard_trend(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db),
) -> DashboardTrendResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	months = [month] if month else range(1, 13)
	
	return DashboardTrendResponse(
		items=[
			DashboardTrendItem(
				year=year or 0,
				month=trend_month,
				revenue=summary.total_revenue,
				cost=summary.total_cost,
				profit=summary.profit,
			)
			for trend_month in months
			for summary in [calculate_company_summary(db, dataset.id, year, trend_month)]
		]
	)


@router.get("/departments", summary="Get department salary and profit analytics", response_model=DepartmentAnalyticsResponse)
def department_analytics(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db),
) -> DepartmentAnalyticsResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	employees = {employee.id: employee for employee in db.query(Employee).filter(Employee.dataset_id == dataset.id).all()}
	entries = _period_filter(db.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset.id), TimesheetEntry, year, month).all()
	
	department_hours_by_employee = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
	total_hours_by_department = defaultdict(lambda: Decimal("0"))
	for entry in entries:
		department_name = entry.department or employees[entry.employee_id].department or "Unassigned"
		department_hours_by_employee[entry.employee_id][department_name] += entry.hours
		total_hours_by_department[department_name] += entry.hours
	
	def employee_department(employee: Employee) -> str:
		hours_by_department = department_hours_by_employee.get(employee.id)
		if hours_by_department:
			return max(hours_by_department.items(), key=lambda item: item[1])[0]
		return employee.department or "Unassigned"
	
	employee_count_by_department = defaultdict(set)
	for employee in employees.values():
		employee_count_by_department[employee_department(employee)].add(employee.id)
	
	total_salary_by_department = defaultdict(lambda: Decimal("0"))
	salary_record_count_by_department = defaultdict(int)
	salary_range_counts = {label: 0 for label, _, _ in SALARY_RANGES}
	salary_query = _period_filter(db.query(MonthlySalary).filter(MonthlySalary.dataset_id == dataset.id), MonthlySalary, year, month)
	for salary in salary_query.all():
		department_name = employee_department(salary.employee)
		total_salary_by_department[department_name] += salary.salary
		salary_record_count_by_department[department_name] += 1
		salary_range_counts[_salary_range(salary.salary)] += 1
	
	billable_categories = {row.name for row in db.query(Category).filter(Category.dataset_id == dataset.id, Category.is_billable.is_(True))}
	projects = {project.id: project for project in db.query(Project).filter(Project.dataset_id == dataset.id).all()}
	project_hours_by_department = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
	total_project_hours = defaultdict(lambda: Decimal("0"))
	for entry in entries:
		if entry.project_id is None or entry.category not in billable_categories:
			continue
		department_name = entry.department or employees[entry.employee_id].department or "Unassigned"
		project_hours_by_department[entry.project_id][department_name] += entry.hours
		total_project_hours[entry.project_id] += entry.hours
	
	revenue_by_department = defaultdict(lambda: Decimal("0"))
	for project_id, department_hours in project_hours_by_department.items():
		project = projects[project_id]
		if project.project_price is None or not _project_revenue_matches_period(project, year, month):
			continue
		project_hours = total_project_hours[project_id]
		if project_hours == 0:
			continue
		for department_name, hours in department_hours.items():
			revenue_by_department[department_name] += project.project_price * hours / project_hours
	
	department_names = sorted(
		set(total_hours_by_department)
		| set(total_salary_by_department)
		| set(revenue_by_department)
		| set(employee_count_by_department)
	)
	departments = []
	for department_name in department_names:
		total_salary = total_salary_by_department[department_name]
		revenue = revenue_by_department[department_name]
		profit = revenue - total_salary
		average_salary = Decimal("0") if salary_record_count_by_department[department_name] == 0 else total_salary / salary_record_count_by_department[department_name]
		departments.append(
			DepartmentAnalyticsItem(
				department=department_name,
				employee_count=len(employee_count_by_department[department_name]),
				total_salary=total_salary,
				average_salary=average_salary,
				revenue=revenue,
				profit=profit,
				margin=None if revenue == 0 else profit / revenue * Decimal("100"),
				total_hours=total_hours_by_department[department_name],
			)
		)
	
	return DepartmentAnalyticsResponse(
		departments=sorted(departments, key=lambda item: item.total_salary, reverse=True),
		salary_ranges=[SalaryRangeItem(range=label, count=count) for label, count in salary_range_counts.items()],
	)
