from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.database import init_db
from backend.app.routes import categories, dashboard, data_quality, datasets, imports, productivity, projects, settings
from backend.app.schemas import HealthResponse


app = FastAPI(
	title="Margin Dashboard",
	version="0.1.0",
	description="REST API for Margin Dashboard - Financial analysis and reporting system",
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(productivity.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(data_quality.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(imports.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
	init_db()


@app.get("/api/health", tags=["health"], response_model=HealthResponse)
def health_check() -> HealthResponse:
	return HealthResponse(status="ok")
