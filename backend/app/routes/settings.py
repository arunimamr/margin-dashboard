from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import MonthlySetting
from backend.app.routes.common import selected_dataset, validate_period
from backend.app.schemas import SettingsListResponse, MonthlySetting as MonthlySettingSchema, SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", summary="Get monthly overhead settings", response_model=SettingsListResponse)
def settings(
	dataset_id: int | None = None,
	year: int | None = None,
	month: int | None = Query(None, ge=1, le=12),
	db: Session = Depends(get_db)
) -> SettingsListResponse:
	validate_period(year, month)
	dataset = selected_dataset(db, dataset_id)
	query = db.query(MonthlySetting).filter(MonthlySetting.dataset_id == dataset.id)
	
	if year is not None:
		query = query.filter(MonthlySetting.year == year)
	if month is not None:
		query = query.filter(MonthlySetting.month == month)
	
	items = [
		MonthlySettingSchema(
			year=row.year,
			month=row.month,
			overhead=row.overhead
		)
		for row in query.order_by(MonthlySetting.year, MonthlySetting.month).all()
	]
	
	return SettingsListResponse(items=items)


@router.put("", summary="Update monthly overhead", response_model=MonthlySettingSchema)
def update_settings(payload: SettingUpdate, db: Session = Depends(get_db)) -> MonthlySettingSchema:
	dataset = selected_dataset(db, payload.dataset_id)
	setting = db.query(MonthlySetting).filter(
		MonthlySetting.dataset_id == dataset.id,
		MonthlySetting.year == payload.year,
		MonthlySetting.month == payload.month
	).first()
	
	if setting is None:
		setting = MonthlySetting(
			dataset_id=dataset.id,
			year=payload.year,
			month=payload.month,
			overhead=payload.overhead
		)
		db.add(setting)
	else:
		setting.overhead = payload.overhead
	
	db.commit()
	
	return MonthlySettingSchema(
		year=setting.year,
		month=setting.month,
		overhead=setting.overhead
	)