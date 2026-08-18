from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from platform.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    phone = Column(String(20), primary_key=True)          # UID
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    gsp_col = Column(Integer, nullable=False)
    gsp_row = Column(Integer, nullable=False)
    premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FileRecord(Base):
    __tablename__ = "files"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)   # 'app', 'game', 'video'

    L = Column(Integer, nullable=False)
    S = Column(Integer, nullable=False)
    c = Column(Integer, nullable=False)
    gsp_col = Column(Integer, nullable=False)
    gsp_row = Column(Integer, nullable=False)

    uploaded_by = Column(String(20), ForeignKey("users.phone"), nullable=False)
    price = Column(Float, default=0.0)
    description = Column(Text, default="")
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_phone = Column(String(20), nullable=False)
    to_phone = Column(String(20), nullable=False)
    body = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_phone = Column(String(20), nullable=False)
    title = Column(String(255), default="")
    body = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_phone = Column(String(20), nullable=False)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    amount = Column(Float, default=0.0)
    reference = Column(String(100), default="")
    status = Column(String(20), default="pending")   # pending, paid, failed
    created_at = Column(DateTime, default=datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"
    user_phone = Column(String(20), primary_key=True)
    language = Column(String(10), default="en")
    notifications_enabled = Column(Boolean, default=True)
    theme = Column(String(20), default="neon-blue")