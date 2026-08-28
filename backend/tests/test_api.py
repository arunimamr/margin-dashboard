from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import Dataset, Employee, MonthlySalary, MonthlySetting, Project, TimesheetEntry, Category


@pytest.fixture
def test_db(tmp_path):
	"""Create test database and yield session."""
	database_path = tmp_path / "test_margin_dashboard.db"
	database_url = f"sqlite:///{database_path.as_posix()}"
	engine = create_engine(database_url, connect_args={"check_same_thread": False})
	Base.metadata.create_all(engine)
	
	session = Session(engine)
	yield session
	session.close()


@pytest.fixture
def client(test_db):
	"""Create test client with test database."""
	def override_get_db():
		yield test_db
	
	app.dependency_overrides[get_db] = override_get_db
	return TestClient(app)


@pytest.fixture
def sample_data(test_db):
	"""Create sample data for testing."""
	# Create dataset
	dataset = Dataset(name="2025 Sample Data", is_active=True)
	test_db.add(dataset)
	test_db.flush()
	
	# Create categories
	billable_cat = Category(dataset=dataset, name="Projects", is_billable=True)
	non_billable_cat = Category(dataset=dataset, name="Admin", is_billable=False)
	test_db.add(billable_cat)
	test_db.add(non_billable_cat)
	test_db.flush()
	
	# Create employees
	emp1 = Employee(dataset=dataset, employee_no="E001", employee_name="Alice Johnson", department="Dev", designation="Developer")
	emp2 = Employee(dataset=dataset, employee_no="E002", employee_name="Bob Smith", department="Sales", designation="Sales Manager")
	test_db.add(emp1)
	test_db.add(emp2)
	test_db.flush()
	
	# Create salary records
	sal1 = MonthlySalary(dataset=dataset, employee=emp1, year=2025, month=1, salary=Decimal("5000.00"))
	sal2 = MonthlySalary(dataset=dataset, employee=emp2, year=2025, month=1, salary=Decimal("6000.00"))
	test_db.add(sal1)
	test_db.add(sal2)
	test_db.flush()
	
	# Create projects
	proj1 = Project(dataset=dataset, ref_code="ABC001", project_name="Project A", project_price=Decimal("100000.00"), sales_month="Jan", category="IT", status="Active")
	proj2 = Project(dataset=dataset, ref_code="ABC002", project_name="Project B", project_price=Decimal("50000.00"), sales_month="Feb", category="IT", status="Active")
	test_db.add(proj1)
	test_db.add(proj2)
	test_db.flush()
	
	# Create timesheet entries
	entry1 = TimesheetEntry(dataset=dataset, employee=emp1, project=proj1, year=2025, month=1, category="Projects", hours=Decimal("160.00"))
	entry2 = TimesheetEntry(dataset=dataset, employee=emp2, project=proj2, year=2025, month=1, category="Projects", hours=Decimal("140.00"))
	entry3 = TimesheetEntry(dataset=dataset, employee=emp1, project=None, year=2025, month=1, category="Admin", hours=Decimal("20.00"))
	test_db.add(entry1)
	test_db.add(entry2)
	test_db.add(entry3)
	
	test_db.commit()
	return dataset


class TestHealth:
	def test_health_check(self, client):
		response = client.get("/api/health")
		assert response.status_code == 200
		assert response.json() == {"status": "ok"}


class TestDatasets:
	def test_get_datasets(self, client, sample_data):
		response = client.get("/api/datasets")
		assert response.status_code == 200
		data = response.json()
		assert "items" in data
		assert len(data["items"]) == 1
		assert data["items"][0]["id"] == sample_data.id
		assert data["items"][0]["name"] == "2025 Sample Data"
		assert data["items"][0]["is_active"] is True
	
	def test_get_dataset_detail(self, client, sample_data):
		response = client.get(f"/api/datasets/{sample_data.id}")
		assert response.status_code == 200
		data = response.json()
		assert data["id"] == sample_data.id
		assert data["name"] == "2025 Sample Data"
		assert "counts" in data
		assert data["counts"]["employees"] == 2
		assert data["counts"]["salary_records"] == 2
		assert data["counts"]["projects"] == 2
		assert data["counts"]["timesheet_entries"] == 3
	
	def test_get_invalid_dataset(self, client):
		response = client.get("/api/datasets/9999")
		assert response.status_code == 404
		assert "Dataset not found" in response.json()["detail"]


class TestDashboard:
	def test_get_dashboard(self, client, sample_data):
		response = client.get("/api/dashboard")
		assert response.status_code == 200
		data = response.json()
		assert data["dataset_id"] == sample_data.id
		assert "period" in data
		assert "hours" in data
		assert "financial" in data
		assert "productivity" in data
		assert "reconciliation" in data
		
		# Check hours (values are serialized as floats)
		assert data["hours"]["total"] == 320.0  # 160 + 140 + 20
		assert data["hours"]["billable"] == 300.0  # 160 + 140
		assert data["hours"]["non_billable"] == 20.0  # 20
	
	def test_get_dashboard_with_dataset_id(self, client, sample_data):
		response = client.get(f"/api/dashboard?dataset_id={sample_data.id}")
		assert response.status_code == 200
		data = response.json()
		assert data["dataset_id"] == sample_data.id
	
	def test_get_dashboard_with_year_month(self, client, sample_data):
		response = client.get(f"/api/dashboard?year=2025&month=1")
		assert response.status_code == 200
		data = response.json()
		assert data["period"]["year"] == 2025
		assert data["period"]["month"] == 1
	
	def test_get_dashboard_invalid_month(self, client):
		response = client.get("/api/dashboard?month=13")
		assert response.status_code == 422  # FastAPI returns 422 for validation errors
		assert "month" in response.json()["detail"][0]["loc"]
	
	def test_dashboard_reconciliation_with_zero_overhead(self, client, sample_data):
		"""Verify that dashboard uses calculation engine and reconciliation passes."""
		response = client.get("/api/dashboard")
		assert response.status_code == 200
		data = response.json()
		# Reconciliation should pass with zero overhead
		assert data["reconciliation"]["passed"] is True
		assert abs(data["reconciliation"]["difference"]) < 0.01  # Allow for floating point precision


class TestProjects:
	def test_get_projects(self, client, sample_data):
		response = client.get("/api/projects")
		assert response.status_code == 200
		data = response.json()
		assert "items" in data
		assert data["total"] == 2
		assert data["page"] == 1
		assert data["page_size"] == 20
		assert len(data["items"]) == 2
	
	def test_get_projects_with_pagination(self, client, sample_data):
		response = client.get("/api/projects?page=1&page_size=1")
		assert response.status_code == 200
		data = response.json()
		assert len(data["items"]) == 1
		assert data["total"] == 2
		assert data["page"] == 1
		assert data["page_size"] == 1
	
	def test_get_projects_with_search(self, client, sample_data):
		response = client.get("/api/projects?search=ABC001")
		assert response.status_code == 200
		data = response.json()
		assert len(data["items"]) == 1
		assert data["items"][0]["ref_code"] == "ABC001"
	
	def test_get_projects_with_status_filter(self, client, sample_data):
		response = client.get("/api/projects?status=profitable")
		assert response.status_code == 200
		data = response.json()
		# All projects should be profitable with the sample data
		assert all(item["status"] == "profitable" for item in data["items"])
	
	def test_get_project_detail(self, client, sample_data):
		response = client.get("/api/projects/ABC001")
		assert response.status_code == 200
		data = response.json()
		assert data["ref_code"] == "ABC001"
		assert data["project_name"] == "Project A"
		assert data["project_price"] == 100000
		assert "employees" in data
	
	def test_get_invalid_project(self, client, sample_data):
		response = client.get("/api/projects/INVALID")
		assert response.status_code == 404
		assert "Project not found" in response.json()["detail"]
	
	def test_project_detail_employees(self, client, sample_data):
		response = client.get("/api/projects/ABC001")
		assert response.status_code == 200
		data = response.json()
		assert "employees" in data
		assert len(data["employees"]) > 0
		emp = data["employees"][0]
		assert "employee_no" in emp
		assert "employee_name" in emp
		assert "hours" in emp
		assert "cost" in emp


class TestProductivity:
	def test_get_productivity(self, client, sample_data):
		response = client.get("/api/productivity")
		assert response.status_code == 200
		data = response.json()
		assert "items" in data
		assert "company_productivity" in data
		assert len(data["items"]) == 2  # Two employees
	
	def test_get_productivity_by_employee(self, client, sample_data):
		response = client.get("/api/productivity?employee_no=E001")
		assert response.status_code == 200
		data = response.json()
		assert len(data["items"]) == 1
		assert data["items"][0]["employee_no"] == "E001"
	
	def test_get_productivity_by_department(self, client, sample_data):
		response = client.get("/api/productivity?department=Dev")
		assert response.status_code == 200
		data = response.json()
		assert all(item["employee_no"] == "E001" for item in data["items"])
	
	def test_productivity_calculation(self, client, sample_data):
		response = client.get("/api/productivity")
		assert response.status_code == 200
		data = response.json()
		# Check that productivity is calculated correctly
		for item in data["items"]:
			total = float(item["total_hours"])  # Convert from string to float
			billable = float(item["billable_hours"])  # Convert from string to float
			if total > 0:
				expected = billable / total * 100
				assert abs(item["productivity"] - expected) < 0.01


class TestCategories:
	def test_get_categories(self, client, sample_data):
		response = client.get("/api/categories")
		assert response.status_code == 200
		data = response.json()
		assert "items" in data
		assert len(data["items"]) >= 2  # At least Projects and Admin
	
	def test_categories_have_billable_flag(self, client, sample_data):
		response = client.get("/api/categories")
		assert response.status_code == 200
		data = response.json()
		for item in data["items"]:
			assert "category" in item
			assert "billable" in item
			assert "hours" in item
			assert "percentage" in item


class TestDataQuality:
	def test_get_data_quality(self, client, sample_data):
		response = client.get("/api/data-quality")
		assert response.status_code == 200
		data = response.json()
		assert data["dataset_id"] == sample_data.id
		assert "errors" in data
		assert "warnings" in data
		assert "summary" in data
		assert "error_count" in data["summary"]
		assert "warning_count" in data["summary"]


class TestSettings:
	def test_get_settings_empty(self, client, sample_data):
		response = client.get("/api/settings")
		assert response.status_code == 200
		data = response.json()
		assert "items" in data
		assert isinstance(data["items"], list)
	
	def test_update_settings(self, client, sample_data, test_db):
		payload = {
			"dataset_id": sample_data.id,
			"year": 2025,
			"month": 1,
			"overhead": 1000.00  # Send as float, not Decimal
		}
		response = client.put("/api/settings", json=payload)
		assert response.status_code == 200
		data = response.json()
		assert data["year"] == 2025
		assert data["month"] == 1
		assert data["overhead"] == 1000.0
	
	def test_get_settings_after_update(self, client, sample_data, test_db):
		# First update
		payload = {
			"dataset_id": sample_data.id,
			"year": 2025,
			"month": 1,
			"overhead": 1000.00  # Send as float
		}
		client.put("/api/settings", json=payload)
		
		# Then get
		response = client.get(f"/api/settings?dataset_id={sample_data.id}")
		assert response.status_code == 200
		data = response.json()
		assert len(data["items"]) == 1
		assert data["items"][0]["year"] == 2025
		assert data["items"][0]["month"] == 1
	
	def test_update_settings_changes_dashboard(self, client, sample_data, test_db):
		"""Verify that changing overhead changes dashboard financial results."""
		# Get dashboard without overhead
		response1 = client.get("/api/dashboard")
		assert response1.status_code == 200
		dashboard1 = response1.json()
		overhead1 = dashboard1["financial"]["overhead"]
		
		# Update overhead
		payload = {
			"dataset_id": sample_data.id,
			"year": 2025,
			"month": 1,
			"overhead": 5000.00  # Send as float
		}
		client.put("/api/settings", json=payload)
		
		# Get dashboard with new overhead
		response2 = client.get("/api/dashboard")
		assert response2.status_code == 200
		dashboard2 = response2.json()
		overhead2 = dashboard2["financial"]["overhead"]
		
		# Overhead should have changed
		assert overhead2 == 5000.0
	
	def test_get_settings_with_year_filter(self, client, sample_data, test_db):
		# Add settings for year 2025 and 2026
		payload1 = {"dataset_id": sample_data.id, "year": 2025, "month": 1, "overhead": 1000.00}
		payload2 = {"dataset_id": sample_data.id, "year": 2026, "month": 1, "overhead": 2000.00}
		client.put("/api/settings", json=payload1)
		client.put("/api/settings", json=payload2)
		
		# Get settings for 2025 only
		response = client.get(f"/api/settings?dataset_id={sample_data.id}&year=2025")
		assert response.status_code == 200
		data = response.json()
		assert len(data["items"]) == 1
		assert data["items"][0]["year"] == 2025
	
	def test_get_settings_with_month_filter(self, client, sample_data, test_db):
		# Add settings for month 1 and 2
		payload1 = {"dataset_id": sample_data.id, "year": 2025, "month": 1, "overhead": 1000.00}
		payload2 = {"dataset_id": sample_data.id, "year": 2025, "month": 2, "overhead": 2000.00}
		client.put("/api/settings", json=payload1)
		client.put("/api/settings", json=payload2)
		
		# Get settings for month 1 only
		response = client.get(f"/api/settings?dataset_id={sample_data.id}&month=1")
		assert response.status_code == 200
		data = response.json()
		assert len(data["items"]) == 1
		assert data["items"][0]["month"] == 1
