from fastapi import FastAPI

from backend.app.database import init_db


app = FastAPI(
    title="Margin Dashboard",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
