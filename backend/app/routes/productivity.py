from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Category, TimesheetEntry
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import DepartmentEmployeeProductivity, DepartmentProductivity, EmployeeProductivity, ProductivityResponse
from backend.app.services.calculations import calculate_employee_monthly_rates, calculate_productivity

router = APIRouter(prefix="/productivity", tags=["productivity"])


@router.get("", summary="Get employee productivity", response_model=ProductivityResponse)
def productivity(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	employee_no: str | None = None,
	department: str | None = None,
	db: Session = Depends(get_db)
) -> ProductivityResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	grouped = defaultdict(lambda: {"total_hours": 0, "billable_hours": 0, "non_billable_hours": 0, "cost": 0})
	department_query = db.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset.id)
	if year is not None:
		department_query = department_query.filter(TimesheetEntry.year == year)
	if month is not None:
		department_query = department_query.filter(TimesheetEntry.month == month)
	entries = department_query.all()
	billable_categories = {row.name for row in db.query(Category).filter(Category.dataset_id == dataset.id, Category.is_billable.is_(True))}
	department_hours_by_employee = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
	for entry in entries:
		if entry.department:
			department_hours_by_employee[entry.employee.employee_no][entry.department] += entry.hours
	department_by_employee = {
		employee_no: max(departments.items(), key=lambda item: item[1])[0]
		for employee_no, departments in department_hours_by_employee.items()
	}
	rates_by_key = {}
	
	for row in calculate_employee_monthly_rates(db, dataset.id, year, month):
		key = row.employee_no
		rates_by_key[(row.employee_no, row.year, row.month)] = row.direct_rate
		grouped[key]["employee_name"] = row.employee_name
		grouped[key]["total_hours"] += row.total_hours
		grouped[key]["billable_hours"] += row.billable_hours
		grouped[key]["non_billable_hours"] += row.non_billable_hours
		grouped[key]["cost"] += row.salary
	
	employees = {employee.employee_no: employee for employee in dataset.employees}
	items = []
	
	for number, values in grouped.items():
		employee = employees[number]
		employee_department = employee.department or department_by_employee.get(number)
		if employee_no and number != employee_no or department and employee_department != department:
			continue
		total = values["total_hours"]
		items.append(
			EmployeeProductivity(
				employee_no=number,
				employee_name=values["employee_name"],
				department=employee_department,
				total_hours=total,
				billable_hours=values["billable_hours"],
				non_billable_hours=values["non_billable_hours"],
				cost=values["cost"],
				productivity=0 if total == 0 else values["billable_hours"] / total * 100
			)
		)

	department_groups = defaultdict(lambda: defaultdict(lambda: {
		"employee_name": "",
		"total_hours": Decimal("0"),
		"billable_hours": Decimal("0"),
		"non_billable_hours": Decimal("0"),
		"cost": Decimal("0"),
	}))
	for entry in entries:
		department_name = entry.department or "Unassigned"
		employee_no = entry.employee.employee_no
		employee_values = department_groups[department_name][employee_no]
		employee_values["employee_name"] = entry.employee.employee_name
		employee_values["total_hours"] += entry.hours
		if entry.category in billable_categories:
			employee_values["billable_hours"] += entry.hours
		else:
			employee_values["non_billable_hours"] += entry.hours
		employee_values["cost"] += entry.hours * rates_by_key.get((employee_no, entry.year, entry.month), Decimal("0"))

	department_items = []
	for department_name, employee_map in department_groups.items():
		employee_items = []
		for employee_no, values in employee_map.items():
			total_hours = values["total_hours"]
			employee_items.append(
				DepartmentEmployeeProductivity(
					employee_no=employee_no,
					employee_name=values["employee_name"],
					total_hours=total_hours,
					billable_hours=values["billable_hours"],
					non_billable_hours=values["non_billable_hours"],
					cost=values["cost"],
					productivity=0 if total_hours == 0 else values["billable_hours"] / total_hours * 100,
				)
			)
		total_department_hours = sum((employee.total_hours for employee in employee_items), Decimal("0"))
		total_department_billable = sum((employee.billable_hours for employee in employee_items), Decimal("0"))
		total_department_non_billable = sum((employee.non_billable_hours for employee in employee_items), Decimal("0"))
		total_department_cost = sum((employee.cost for employee in employee_items), Decimal("0"))
		department_items.append(
			DepartmentProductivity(
				name=department_name,
				people=len(employee_items),
				total_hours=total_department_hours,
				billable_hours=total_department_billable,
				non_billable_hours=total_department_non_billable,
				cost=total_department_cost,
				productivity=0 if total_department_hours == 0 else total_department_billable / total_department_hours * 100,
				employees=sorted(employee_items, key=lambda employee: employee.total_hours, reverse=True),
			)
		)
	
	return ProductivityResponse(
		items=items,
		departments=sorted(department_items, key=lambda item: item.total_hours, reverse=True),
		company_productivity=calculate_productivity(db, dataset.id, year, month)
	)
