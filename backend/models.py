from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    phone = Column(String(20), primary_key=True)          # UID
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    gsp_col = Column(Integer, nullable=False)
    gsp_row = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FileRecord(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)

    # Object placement
    L = Column(Integer, nullable=False)
    S = Column(Integer, nullable=False)
    c = Column(Integer, nullable=False)
    gsp_col = Column(Integer, nullable=False)
    gsp_row = Column(Integer, nullable=False)

    uploaded_by = Column(String(20), nullable=False)      # phone of uploader
    price = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)