from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SignupRequest(BaseModel):
    full_name: str
    phone: str
    password: str

class LoginRequest(BaseModel):
    phone: str
    password: str

class UploadResponse(BaseModel):
    id: str
    filename: str
    category: str
    gsp_col: int
    gsp_row: int
    price: float
    download_url: str
    created_at: datetime

class FileOut(BaseModel):
    id: str
    filename: str
    category: str
    gsp_col: int
    gsp_row: int
    size_bytes: int
    uploaded_by: str
    price: float
    download_count: int
    description: str
    created_at: datetime

    class Config:
        orm_mode = True

class MessageOut(BaseModel):
    id: str
    from_phone: str
    to_phone: str
    body: str
    created_at: datetime

    class Config:
        orm_mode = True

class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True

class PaymentOut(BaseModel):
    id: str
    file_id: str
    amount: float
    reference: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True