# Margin Dashboard

Margin Dashboard is a project profitability and productivity dashboard for finance and delivery teams. It imports timesheet, salary, and project price Excel files, calculates margins and employee cost allocation, and presents the results through a React dashboard backed by a FastAPI API.


## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, pandas
- Frontend: React, Vite, React Router, Recharts
- Database: `backend/data/margin_dashboard.db`
- API style: REST over JSON

## Quick Start

Start the backend first, then the frontend.

### Backend

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python run.py
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python run.py
```

Backend URL:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## Sample Data

Sample files are available in `sample-data/`:

- `timesheet-2025.xlsx`
- `salaries-2025.xlsx`
- `project-prices-2025.xlsx`

Use the Import Data page to upload all three files together and create a dataset.

## Import File Requirements

The importer expects these sheets:

- Timesheet file: sheet named `Timesheet`
- Salary file: sheet named `Salary`
- Project price file: sheet named `Projects`

Required timesheet columns:

- `Month`
- `Employee No`
- `Employee Name`
- `Department`
- `Designation`
- `Category`
- `Ref Code`
- `Project Billable Task Unbillable Name`
- `Description`
- `Hours`

Required salary columns:

- `Employee No`
- `Employee Name`
- Month columns such as `January`, `February`, etc.

Required project columns:

- `Ref Code`
- `Project Billable Name`
- `Project Price`
- `Sales Month`
- `Category`
- `Status`

Employee numbers are preserved as IDs with leading zeroes, for example `00102`.

## API Endpoints

All API endpoints are served from `http://127.0.0.1:8000`.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Backend health check |
| GET | `/api/datasets` | List datasets |
| GET | `/api/datasets/{dataset_id}` | Get dataset metadata and record counts |
| POST | `/api/import` | Import timesheet, salary, and project files |
| GET | `/api/dashboard` | Company KPI summary |
| GET | `/api/dashboard/trend` | Monthly revenue, cost, and profit trend |
| GET | `/api/dashboard/departments` | Department salary and profit analytics |
| GET | `/api/projects` | Project profitability list |
| GET | `/api/projects/{ref_code}` | Project profitability detail |
| GET | `/api/productivity` | Employee productivity and department drill-down data |
| GET | `/api/categories` | Category hour summaries |
| GET | `/api/categories/matrix` | Employee x category matrix |
| GET | `/api/employees/{employee_no}` | Employee department, designation, hours, and monthly salaries |
| GET | `/api/data-quality` | Dataset data-quality issues |
| GET | `/api/settings` | Monthly overhead settings |
| PUT | `/api/settings` | Update monthly overhead |

Common query parameters:

- `dataset_id`
- `year`
- `month`

Some endpoints support additional filters, such as `status`, `category`, `search`, `employee_no`, and `department`.

## Development Workflow

1. Start the backend from the project root with `python run.py`.
2. Start the frontend from `frontend/` with `npm run dev`.
3. Open `http://127.0.0.1:5173`.
4. Import a dataset or select an existing dataset from the dashboard filters.

Build the frontend:

```bash
cd frontend
npm run build
```

Run backend tests when test dependencies are installed:

```bash
python -m pytest backend/tests
```

If `pytest` is not installed:

```bash
pip install pytest
```

## Notes

- The backend must be running before the frontend can load dashboard data.
- CORS is configured for local frontend ports on `localhost` and `127.0.0.1`.
- Imported datasets are stored in SQLite under `backend/data/`.
- The app uses uploaded data and API responses for dashboard values; dashboard pages should not rely on hardcoded KPI data.
