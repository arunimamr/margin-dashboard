import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import ImportResponse
from backend.app.services.data_quality import ImportValidationError
from backend.app.services.importer import import_dataset

router = APIRouter(tags=["imports"])


@router.post("/import", response_model=ImportResponse, summary="Import a dataset from three Excel files")
async def import_files(dataset_name: str = Form(...), timesheet: UploadFile = File(...), salary: UploadFile = File(...), project: UploadFile = File(...), db: Session = Depends(get_db)):
    suffixes = {"timesheet": ".xlsx", "salary": ".xlsx", "project": ".xlsx"}
    paths: dict[str, Path] = {}
    try:
        for key, upload in (("timesheet", timesheet), ("salary", salary), ("project", project)):
            if not upload.filename or not upload.filename.lower().endswith((".xlsx", ".xls")):
                raise HTTPException(status_code=400, detail=f"Invalid {key} upload")
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffixes[key])
            paths[key] = Path(handle.name)
            handle.write(await upload.read())
            handle.close()
        return import_dataset(paths["timesheet"], paths["salary"], paths["project"], dataset_name, session=db)
    except ImportValidationError as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc), **exc.report.as_dict()}) from exc
    finally:
        for path in paths.values():
            path.unlink(missing_ok=True)