from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Employee, MonthlySalary, TimesheetEntry
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import EmployeeDetailResponse, EmployeeMonthlySalaryItem

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/{employee_no}", summary="Get employee detail", response_model=EmployeeDetailResponse)
def employee_detail(
	employee_no: str,
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db),
) -> EmployeeDetailResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	employee = db.query(Employee).filter(Employee.dataset_id == dataset.id, Employee.employee_no == employee_no).first()
	
	if employee is None:
		raise HTTPException(status_code=404, detail="Employee not found")
	
	timesheet_query = db.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset.id, TimesheetEntry.employee_id == employee.id)
	if year is not None:
		timesheet_query = timesheet_query.filter(TimesheetEntry.year == year)
	if month is not None:
		timesheet_query = timesheet_query.filter(TimesheetEntry.month == month)
	timesheet_entries = timesheet_query.all()
	total_working_hours = sum((entry.hours for entry in timesheet_entries), Decimal("0"))
	
	department_hours = defaultdict(lambda: Decimal("0"))
	for entry in timesheet_entries:
		if entry.department:
			department_hours[entry.department] += entry.hours
	department = employee.department or (max(department_hours.items(), key=lambda item: item[1])[0] if department_hours else None)
	
	salary_query = db.query(MonthlySalary).filter(MonthlySalary.dataset_id == dataset.id, MonthlySalary.employee_id == employee.id)
	if year is not None:
		salary_query = salary_query.filter(MonthlySalary.year == year)
	monthly_salaries = [
		EmployeeMonthlySalaryItem(year=row.year, month=row.month, salary=row.salary)
		for row in salary_query.order_by(MonthlySalary.year, MonthlySalary.month).all()
	]
	
	return EmployeeDetailResponse(
		employee_no=employee.employee_no,
		employee_name=employee.employee_name,
		department=department,
		designation=employee.designation,
		total_working_hours=total_working_hours,
		monthly_salaries=monthly_salaries,
	)
