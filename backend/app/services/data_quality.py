from dataclasses import dataclass, field
from typing import Any


@dataclass
class DataQualityReport:
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def as_dict(self) -> dict[str, list[str]]:
        return {"warnings": self.warnings, "errors": self.errors}


class ImportValidationError(ValueError):
    def __init__(self, message: str, report: DataQualityReport | None = None):
        super().__init__(message)
        self.report = report or DataQualityReport(errors=[message])


def validate_required_columns(frame: Any, required: set[str], source: str, report: DataQualityReport) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        report.error(f"{source} is missing required columns: {', '.join(missing)}")