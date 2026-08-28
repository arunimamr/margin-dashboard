from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services.importer import import_dataset


def main() -> None:
    result = import_dataset(
        ROOT / "sample-data" / "timesheet-2025.xlsx",
        ROOT / "sample-data" / "salaries-2025.xlsx",
        ROOT / "sample-data" / "project-prices-2025.xlsx",
        "2025 Sample Data",
    )
    print("========================================")
    print("DATA IMPORT RESULT")
    print("========================================")
    print(f"Dataset: {result['dataset_id']}")
    print(f"Employees: {result['employees_imported']}")
    print(f"Salary records: {result['salary_records_imported']}")
    print(f"Projects: {result['projects_imported']}")
    print(f"Timesheet entries: {result['timesheet_rows_imported']}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"Errors: {len(result['errors'])}")
    print("========================================")


if __name__ == "__main__":
    main()