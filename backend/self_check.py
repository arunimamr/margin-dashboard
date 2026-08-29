import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import Session

from backend.app.database import engine, init_db
from backend.app.models import Dataset
from backend.app.services.calculations import calculate_company_summary, calculate_project_summary, reconcile_company_cost, reconcile_project_costs


def main() -> None:
	init_db()
	with Session(engine) as session:
		dataset = session.query(Dataset).order_by(Dataset.id.desc()).first()
		if dataset is None:
			print("No dataset found. Run `python backend/import_sample_data.py` first.")
			return
		summary = calculate_company_summary(session, dataset.id)
		projects = calculate_project_summary(session, dataset.id)
		reconciliation = reconcile_company_cost(session, dataset.id)
		project_reconciliation = reconcile_project_costs(session, dataset.id)
		print("========================================")
		print(f"{dataset.name.upper()} PROJECTS DASHBOARD SELF CHECK")
		print("========================================")
		print("DATA")
		print("----------------------------------------")
		print(f"Employees: {len(dataset.employees)}")
		print(f"Projects: {len(dataset.projects)}")
		print(f"Timesheet entries: {len(dataset.timesheet_entries)}")
		print("\nHOURS")
		print("----------------------------------------")
		print(f"Total logged hours: {summary.total_hours}")
		print(f"Billable hours: {summary.billable_hours}")
		print(f"Non-billable hours: {summary.non_billable_hours}")
		print("\nFINANCIAL")
		print("----------------------------------------")
		print(f"Total salaries: AED {summary.total_salary:,.2f}")
		print(f"Total project revenue: AED {summary.total_revenue:,.2f}")
		print(f"Total overhead: AED {summary.overhead:,.2f}")
		print("\nCALCULATED")
		print("----------------------------------------")
		print(f"Indirect cost pool: AED {summary.indirect_pool:,.2f}")
		print(f"Calculated company cost: AED {summary.calculated_company_cost:,.2f}")
		print(f"Company profit: AED {summary.profit:,.2f}")
		print(f"Company margin: {summary.margin:.2f}%" if summary.margin is not None else "Company margin: N/A")
		print("\nRECONCILIATION")
		print("----------------------------------------")
		print(f"Expected salary cost: AED {reconciliation['total_salary']:,.2f}")
		print(f"Calculated company cost: AED {reconciliation['calculated_company_cost']:,.2f}")
		print(f"Difference: AED {reconciliation['difference']:,.2f}")
		print(f"Status: {'PASS' if reconciliation['passed'] else 'FAIL'}")
		print(f"Project allocation difference: AED {project_reconciliation['difference']:,.2f}")
		print(f"Project allocation status: {'PASS' if project_reconciliation['passed'] else 'FAIL'}")
		print("\nPROJECT PROFITABILITY")
		print("----------------------------------------")
		print("Ref Code | Project | Revenue | Cost | Profit | Margin")
		for project in projects:
			revenue = "N/A" if project.project_price is None else f"AED {project.project_price:,.2f}"
			profit = "N/A" if project.profit is None else f"AED {project.profit:,.2f}"
			margin = "N/A" if project.margin is None else f"{project.margin:.2f}%"
			print(f"{project.ref_code} | {project.project_name or 'N/A'} | {revenue} | AED {project.total_cost:,.2f} | {profit} | {margin}")
		print("========================================")


if __name__ == "__main__":
	main()
