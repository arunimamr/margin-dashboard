from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import DashboardResponse, PeriodInfo, HoursInfo, FinancialInfo, ReconciliationInfo
from backend.app.services.calculations import calculate_company_summary, reconcile_company_cost
from backend.app.routes.common import selected_dataset, validate_period

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


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
	reconciliation = reconcile_company_cost(db, dataset.id, year, month)
	
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
			expected_salary_cost=reconciliation["total_salary"],
			calculated_company_cost=reconciliation["calculated_company_cost"],
			difference=reconciliation["difference"],
			passed=reconciliation["passed"]
		)
	)