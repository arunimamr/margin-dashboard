from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models import Dataset


def selected_dataset(session: Session, dataset_id: int | None) -> Dataset:
    dataset = session.get(Dataset, dataset_id) if dataset_id is not None else session.query(Dataset).filter(Dataset.is_active.is_(True)).first()
    if dataset is None and dataset_id is None:
        dataset = session.query(Dataset).order_by(Dataset.id.desc()).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def validate_period(year: int | None, month: int | None) -> None:
    if year is not None and year < 1:
        raise HTTPException(status_code=400, detail="year must be positive")
    if month is not None and not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")