from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import TimesheetEntry
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import CategoriesListResponse, CategoryMatrixColumn, CategoryMatrixResponse, CategoryMatrixRow, CategorySummaryItem
from backend.app.services.calculations import calculate_category_summary

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", summary="Get category hour summaries", response_model=CategoriesListResponse)
def categories(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db)
) -> CategoriesListResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	rows = calculate_category_summary(db, dataset.id, year, month)
	items = [
		CategorySummaryItem(
			category=row.category,
			billable=row.is_billable,
			hours=row.total_hours,
			percentage=row.percentage
		)
		for row in rows
	]
	return CategoriesListResponse(items=items)


@router.get("/matrix", summary="Get employee by category matrix", response_model=CategoryMatrixResponse)
def category_matrix(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db)
) -> CategoryMatrixResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	category_rows = sorted(
		calculate_category_summary(db, dataset.id, year, month),
		key=lambda row: (not row.is_billable, -row.percentage, row.category.lower()),
	)
	query = db.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset.id)
	if year is not None:
		query = query.filter(TimesheetEntry.year == year)
	if month is not None:
		query = query.filter(TimesheetEntry.month == month)
	
	employee_rows = defaultdict(lambda: {
		"employee_name": "",
		"department_hours": defaultdict(lambda: Decimal("0")),
		"categories": defaultdict(lambda: Decimal("0")),
		"total_hours": Decimal("0"),
	})
	
	for entry in query.all():
		employee_no = entry.employee.employee_no
		values = employee_rows[employee_no]
		values["employee_name"] = entry.employee.employee_name
		values["categories"][entry.category] += entry.hours
		values["total_hours"] += entry.hours
		if entry.department:
			values["department_hours"][entry.department] += entry.hours
	
	columns = [
		CategoryMatrixColumn(
			category=row.category,
			billable=row.is_billable,
			hours=row.total_hours,
			percentage=row.percentage,
		)
		for row in category_rows
	]
	
	rows = []
	for employee_no, values in employee_rows.items():
		department = None
		if values["department_hours"]:
			department = max(values["department_hours"].items(), key=lambda item: item[1])[0]
		rows.append(
			CategoryMatrixRow(
				employee_no=employee_no,
				employee_name=values["employee_name"],
				department=department,
				total_hours=values["total_hours"],
				categories={column.category: values["categories"].get(column.category, Decimal("0")) for column in columns},
			)
		)
	
	return CategoryMatrixResponse(
		columns=columns,
		rows=sorted(rows, key=lambda row: row.total_hours, reverse=True),
	)
