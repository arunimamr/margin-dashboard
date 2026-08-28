from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Dataset, Employee, MonthlySalary, Project, TimesheetEntry
from backend.app.schemas import DatasetsListResponse, DatasetResponse, DatasetDetailResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", summary="List datasets", response_model=DatasetsListResponse)
def datasets(db: Session = Depends(get_db)) -> DatasetsListResponse:
	rows = db.query(Dataset).order_by(Dataset.id).all()
	items = [
		DatasetResponse(
			id=row.id,
			name=row.name,
			created_at=row.created_at,
			is_active=row.is_active
		)
		for row in rows
	]
	return DatasetsListResponse(items=items)


@router.get("/{dataset_id}", summary="Get dataset metadata", response_model=DatasetDetailResponse)
def dataset_detail(dataset_id: int, db: Session = Depends(get_db)) -> DatasetDetailResponse:
	dataset = db.get(Dataset, dataset_id)
	if dataset is None:
		raise HTTPException(status_code=404, detail="Dataset not found")
	
	counts = {
		"employees": db.query(Employee).filter(Employee.dataset_id == dataset.id).count(),
		"salary_records": db.query(MonthlySalary).filter(MonthlySalary.dataset_id == dataset.id).count(),
		"projects": db.query(Project).filter(Project.dataset_id == dataset.id).count(),
		"timesheet_entries": db.query(TimesheetEntry).filter(TimesheetEntry.dataset_id == dataset.id).count(),
	}
	
	return DatasetDetailResponse(
		id=dataset.id,
		name=dataset.name,
		created_at=dataset.created_at,
		is_active=dataset.is_active,
		counts=counts
	)