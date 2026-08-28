from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import CategoriesListResponse, CategorySummaryItem
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