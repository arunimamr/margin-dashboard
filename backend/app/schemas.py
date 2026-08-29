from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_serializer


# Health Check
class HealthResponse(BaseModel):
	status: str


# Dataset
class DatasetResponse(BaseModel):
	id: int
	name: str
	created_at: datetime
	is_active: bool


class DatasetDetailResponse(BaseModel):
	id: int
	name: str
	created_at: datetime
	is_active: bool
	counts: dict[str, int]


class DatasetsListResponse(BaseModel):
	items: list[DatasetResponse]


# Dashboard
class PeriodInfo(BaseModel):
	year: Optional[int] = None
	month: Optional[int] = None


class HoursInfo(BaseModel):
	total: Decimal
	billable: Decimal
	non_billable: Decimal
	
	@field_serializer('total', 'billable', 'non_billable')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class FinancialInfo(BaseModel):
	revenue: Decimal
	cost: Decimal
	profit: Decimal
	margin: Optional[Decimal] = None
	overhead: Decimal
	
	@field_serializer('revenue', 'cost', 'profit', 'margin', 'overhead')
	def serialize_decimal(self, value: Decimal) -> Optional[float]:
		return float(value) if value is not None else None


class ReconciliationInfo(BaseModel):
	expected_salary_cost: Decimal
	calculated_company_cost: Decimal
	difference: Decimal
	passed: bool
	
	@field_serializer('expected_salary_cost', 'calculated_company_cost', 'difference')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class DashboardResponse(BaseModel):
	dataset_id: int
	period: PeriodInfo
	hours: HoursInfo
	financial: FinancialInfo
	productivity: Decimal
	reconciliation: ReconciliationInfo
	
	@field_serializer('productivity')
	def serialize_productivity(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class DashboardTrendItem(BaseModel):
	year: int
	month: int
	revenue: Decimal
	cost: Decimal
	profit: Decimal
	
	@field_serializer('revenue', 'cost', 'profit')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class DashboardTrendResponse(BaseModel):
	items: list[DashboardTrendItem]


# Projects
class ProjectSummaryItem(BaseModel):
	ref_code: str
	project_name: Optional[str] = None
	revenue: Optional[Decimal] = None
	cost: Decimal
	profit: Optional[Decimal] = None
	margin: Optional[Decimal] = None
	hours: Decimal
	status: str
	
	@field_serializer('revenue', 'cost', 'profit', 'margin', 'hours')
	def serialize_decimal(self, value: Decimal) -> Optional[float]:
		return float(value) if value is not None else None


class ProjectsListResponse(BaseModel):
	items: list[ProjectSummaryItem]
	total: int
	page: int
	page_size: int


class EmployeeProjectProfitability(BaseModel):
	employee_no: str
	employee_name: str
	hours: Decimal
	direct_rate: Optional[Decimal] = None
	indirect_rate: Optional[Decimal] = None
	cost: Decimal
	revenue_share: Optional[Decimal] = None
	profitability: Optional[Decimal] = None
	
	@field_serializer('hours', 'direct_rate', 'indirect_rate', 'cost', 'revenue_share', 'profitability')
	def serialize_decimal(self, value: Decimal) -> Optional[float]:
		return float(value) if value is not None else None


class ProjectDetailResponse(BaseModel):
	ref_code: str
	project_name: Optional[str] = None
	category: Optional[str] = None
	project_price: Optional[Decimal] = None
	total_project_hours: Decimal
	total_project_cost: Decimal
	profit: Optional[Decimal] = None
	margin: Optional[Decimal] = None
	status: str
	employees: list[EmployeeProjectProfitability]
	
	@field_serializer('project_price', 'total_project_hours', 'total_project_cost', 'profit', 'margin')
	def serialize_decimal(self, value: Decimal) -> Optional[float]:
		return float(value) if value is not None else None


# Productivity
class EmployeeProductivity(BaseModel):
	employee_no: str
	employee_name: str
	department: Optional[str] = None
	total_hours: Decimal
	billable_hours: Decimal
	non_billable_hours: Decimal
	cost: Decimal
	productivity: Decimal
	
	@field_serializer('total_hours', 'billable_hours', 'non_billable_hours', 'cost', 'productivity')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class DepartmentEmployeeProductivity(BaseModel):
	employee_no: str
	employee_name: str
	total_hours: Decimal
	billable_hours: Decimal
	non_billable_hours: Decimal
	cost: Decimal
	productivity: Decimal
	
	@field_serializer('total_hours', 'billable_hours', 'non_billable_hours', 'cost', 'productivity')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class DepartmentProductivity(BaseModel):
	name: str
	people: int
	total_hours: Decimal
	billable_hours: Decimal
	non_billable_hours: Decimal
	cost: Decimal
	productivity: Decimal
	employees: list[DepartmentEmployeeProductivity]
	
	@field_serializer('total_hours', 'billable_hours', 'non_billable_hours', 'cost', 'productivity')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class ProductivityResponse(BaseModel):
	items: list[EmployeeProductivity]
	departments: list[DepartmentProductivity] = []
	company_productivity: Decimal
	
	@field_serializer('company_productivity')
	def serialize_productivity(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class DepartmentAnalyticsItem(BaseModel):
	department: str
	employee_count: int
	total_salary: Decimal
	average_salary: Decimal
	revenue: Decimal
	profit: Decimal
	margin: Optional[Decimal] = None
	total_hours: Decimal
	
	@field_serializer('total_salary', 'average_salary', 'revenue', 'profit', 'margin', 'total_hours')
	def serialize_decimal(self, value: Decimal) -> Optional[float]:
		return float(value) if value is not None else None


class SalaryRangeItem(BaseModel):
	range: str
	count: int


class DepartmentAnalyticsResponse(BaseModel):
	departments: list[DepartmentAnalyticsItem]
	salary_ranges: list[SalaryRangeItem]


class EmployeeMonthlySalaryItem(BaseModel):
	year: int
	month: int
	salary: Decimal
	
	@field_serializer('salary')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class EmployeeDetailResponse(BaseModel):
	employee_no: str
	employee_name: str
	department: Optional[str] = None
	designation: Optional[str] = None
	total_working_hours: Decimal
	monthly_salaries: list[EmployeeMonthlySalaryItem]
	
	@field_serializer('total_working_hours')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


# Categories
class CategorySummaryItem(BaseModel):
	category: str
	billable: bool
	hours: Decimal
	percentage: Decimal
	
	@field_serializer('hours', 'percentage')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class CategoriesListResponse(BaseModel):
	items: list[CategorySummaryItem]


class CategoryMatrixColumn(BaseModel):
	category: str
	billable: bool
	hours: Decimal
	percentage: Decimal
	
	@field_serializer('hours', 'percentage')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class CategoryMatrixRow(BaseModel):
	employee_no: str
	employee_name: str
	department: Optional[str] = None
	total_hours: Decimal
	categories: dict[str, Decimal]
	
	@field_serializer('total_hours')
	def serialize_total_hours(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0
	
	@field_serializer('categories')
	def serialize_categories(self, value: dict[str, Decimal]) -> dict[str, float]:
		return {key: float(amount) for key, amount in value.items()}


class CategoryMatrixResponse(BaseModel):
	columns: list[CategoryMatrixColumn]
	rows: list[CategoryMatrixRow]


# Settings
class MonthlySetting(BaseModel):
	year: int
	month: int
	overhead: Decimal
	
	@field_serializer('overhead')
	def serialize_decimal(self, value: Decimal) -> float:
		return float(value) if value is not None else 0.0


class SettingsListResponse(BaseModel):
	items: list[MonthlySetting]


class SettingUpdate(BaseModel):
	dataset_id: int
	year: int = Field(ge=1)
	month: int = Field(ge=1, le=12)
	overhead: Decimal = Field(ge=0)


# Data Quality
class DataQualityResponse(BaseModel):
	dataset_id: int
	errors: list[str]
	warnings: list[str]
	summary: dict[str, int]


# Import
class ImportResponse(BaseModel):
	status: str
	dataset_id: int
	employees_imported: int
	salary_records_imported: int
	projects_imported: int
	timesheet_rows_imported: int
	warnings: list[str] = []
	errors: list[str] = []
