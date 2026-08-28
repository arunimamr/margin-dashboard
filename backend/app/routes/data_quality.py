from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import MonthlySalary, TimesheetEntry
from backend.app.routes.common import selected_dataset
from backend.app.schemas import DataQualityResponse

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


@router.get("", summary="Get dataset data-quality issues", response_model=DataQualityResponse)
def data_quality(dataset_id: int | None = None, db: Session = Depends(get_db)) -> DataQualityResponse:
	dataset = selected_dataset(db, dataset_id)
	warnings: list[str] = []
	salary_employee_ids = {row.employee_id for row in db.query(MonthlySalary).filter(MonthlySalary.dataset_id == dataset.id).all()}
	
	for entry in db.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset.id).all():
		if entry.employee_id not in salary_employee_ids:
			warnings.append(f"Timesheet employee has no salary: {entry.employee.employee_no}")
		if entry.project_id is None:
			warnings.append(f"Timesheet entry has no matching project: {entry.task_name or 'unknown'}")
	
	errors: list[str] = []
	
	return DataQualityResponse(
		dataset_id=dataset.id,
		errors=errors,
		warnings=warnings,
		summary={
			"error_count": len(errors),
			"warning_count": len(warnings)
		}
	)