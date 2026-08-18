from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SignupRequest(BaseModel):
    full_name: str
    phone: str
    password: str

class SignupResponse(BaseModel):
    message: str
    gsp_col: int
    gsp_row: int

class UploadResponse(BaseModel):
    id: UUID
    filename: str
    L: int
    S: int
    c: int
    gsp_col: int
    gsp_row: int
    price: float
    download_url: str

    class Config:
        orm_mode = True

class FileSearchResult(BaseModel):
    id: UUID
    filename: str
    gsp_col: int
    gsp_row: int
    price: float
    download_count: int
    description: Optional[str]
    uploaded_by: str
    created_at: datetime

    class Config:
        orm_mode = True