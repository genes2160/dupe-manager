from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ScanRequest(BaseModel):
    root_path: str = Field(..., description="Directory to scan")
    extensions: Optional[List[str]] = Field(
        default=None,
        description="Optional list of extensions like ['pdf', '.txt']. None means all files.",
    )


class ScanResponse(BaseModel):
    scan_id: str
    status: Literal["queued", "running", "completed", "failed"]
    message: str | None = None


class ScanStatus(BaseModel):
    scan_id: str
    status: str
    total_files: int
    scanned_files: int
    message: str | None = None


class DuplicateItem(BaseModel):
    filename: str
    size_bytes: int
    path: str


class DuplicateGroup(BaseModel):
    dup_key: str
    filename: str
    size_bytes: int
    items: List[DuplicateItem]


class DeleteChoice(BaseModel):
    path: str
    action: Literal["delete", "skip"]


class DeleteRequest(BaseModel):
    scan_id: str
    choices: List[DeleteChoice]
