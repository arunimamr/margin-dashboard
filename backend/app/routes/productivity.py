from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import ProductivityResponse, EmployeeProductivity
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
	grouped = defaultdict(lambda: {"total_hours": 0, "billable_hours": 0, "non_billable_hours": 0, "salary": 0})
	
	for row in calculate_employee_monthly_rates(db, dataset.id, year, month):
		key = row.employee_no
		grouped[key]["employee_name"] = row.employee_name
		grouped[key]["total_hours"] += row.total_hours
		grouped[key]["billable_hours"] += row.billable_hours
		grouped[key]["non_billable_hours"] += row.non_billable_hours
	
	employees = {employee.employee_no: employee for employee in dataset.employees}
	items = []
	
	for number, values in grouped.items():
		employee = employees[number]
		if employee_no and number != employee_no or department and employee.department != department:
			continue
		total = values["total_hours"]
		items.append(
			EmployeeProductivity(
				employee_no=number,
				employee_name=values["employee_name"],
				total_hours=total,
				billable_hours=values["billable_hours"],
				non_billable_hours=values["non_billable_hours"],
				productivity=0 if total == 0 else values["billable_hours"] / total * 100
			)
		)
	
	return ProductivityResponse(
		items=items,
		company_productivity=calculate_productivity(db, dataset.id, year, month)
	)