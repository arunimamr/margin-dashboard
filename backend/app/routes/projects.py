from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Project
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import ProjectsListResponse, ProjectSummaryItem, ProjectDetailResponse, EmployeeProjectProfitability
from backend.app.services.calculations import calculate_project_employee_cost, calculate_project_summary, calculate_indirect_rate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", summary="List project profitability", response_model=ProjectsListResponse)
def projects(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	category: str | None = None,
	status: str | None = None,
	profitable: bool | None = None,
	search: str | None = None,
	page: int = Query(1, ge=1),
	page_size: int = Query(20, ge=1, le=100),
	db: Session = Depends(get_db)
) -> ProjectsListResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	rows = calculate_project_summary(db, dataset.id, year, month)
	
	if category:
		rows = [row for row in rows if next((project.category for project in dataset.projects if project.ref_code == row.ref_code), None) == category]
	if status:
		rows = [row for row in rows if row.status.lower() == status.lower()]
	if profitable is not None:
		rows = [row for row in rows if (row.status == "profitable") == profitable]
	if search:
		needle = search.lower()
		rows = [row for row in rows if needle in row.ref_code.lower() or needle in (row.project_name or "").lower()]
	
	total = len(rows)
	start = (page - 1) * page_size
	items = [
		ProjectSummaryItem(
			ref_code=row.ref_code,
			project_name=row.project_name,
			revenue=row.project_price,
			cost=row.total_cost,
			profit=row.profit,
			margin=row.margin,
			hours=row.total_hours,
			status=row.status
		)
		for row in rows[start : start + page_size]
	]
	
	return ProjectsListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{ref_code}", summary="Get project profitability detail", response_model=ProjectDetailResponse)
def project_detail(
	ref_code: str,
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db)
) -> ProjectDetailResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	project = db.query(Project).filter(Project.dataset_id == dataset.id, Project.ref_code == ref_code).first()
	
	if project is None:
		raise HTTPException(status_code=404, detail="Project not found")
	
	summary = next((row for row in calculate_project_summary(db, dataset.id, year, month) if row.ref_code == ref_code), None)
	
	if summary is None:
		raise HTTPException(status_code=404, detail="Project not found")
	
	indirect_rate = calculate_indirect_rate(db, dataset.id, year, month)
	employees = [row for row in calculate_project_employee_cost(db, dataset.id, year, month) if row.ref_code == ref_code]
	
	employee_items = [
		EmployeeProjectProfitability(
			employee_no=row.employee_no,
			employee_name=row.employee_name,
			hours=row.project_hours,
			direct_rate=row.direct_rate,
			indirect_rate=indirect_rate,
			cost=row.employee_cost,
			revenue_share=row.revenue_share,
			profitability=row.profitability
		)
		for row in employees
	]
	
	return ProjectDetailResponse(
		ref_code=ref_code,
		project_name=project.project_name,
		category=project.category,
		project_price=summary.project_price,
		total_project_hours=summary.total_hours,
		total_project_cost=summary.total_cost,
		profit=summary.profit,
		margin=summary.margin,
		status=summary.status,
		employees=employee_items
	)
