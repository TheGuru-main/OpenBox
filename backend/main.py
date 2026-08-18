import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List

from models import Base, User, FileRecord
from schemas import SignupRequest, SignupResponse, UploadResponse, FileSearchResult
from gsp import user_placement, object_placement, name_length, digit_sum, first_letter_index

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/openbox")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenBox", version="1.0.0")

# Serve static frontend at root
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r") as f:
        return f.read()

app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/signup", response_model=SignupResponse)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    # Check existing user
    existing = db.query(User).filter(User.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="Phone already registered")

    # Compute user placement
    cell = user_placement(payload.full_name, payload.phone)

    user = User(
        phone=payload.phone,
        full_name=payload.full_name,
        password_hash=payload.password,   # in production use hash
        gsp_col=cell["col"],
        gsp_row=cell["row"]
    )
    db.add(user)
    db.commit()

    return SignupResponse(message="User created", gsp_col=cell["col"], gsp_row=cell["row"])

@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
    price: float = Form(0.0),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    # Verify uploader exists
    user = db.query(User).filter(User.phone == uploaded_by).first()
    if not user:
        raise HTTPException(status_code=404, detail="Uploader not registered")

    # Save file
    file_id = uuid.uuid4()
    ext = os.path.splitext(file.filename)[1]
    storage_name = f"{file_id}{ext}"
    storage_path = os.path.join(UPLOAD_DIR, storage_name)

    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    size_bytes = os.path.getsize(storage_path)

    # Compute object placement
    cell = object_placement(file.filename)
    L = name_length(file.filename)
    S = digit_sum("550198550199")
    c = first_letter_index(file.filename)

    record = FileRecord(
        id=file_id,
        filename=file.filename,
        storage_path=storage_path,
        size_bytes=size_bytes,
        content_type=file.content_type,
        L=L,
        S=S,
        c=c,
        gsp_col=cell["col"],
        gsp_row=cell["row"],
        uploaded_by=uploaded_by,
        price=price,
        description=description
    )
    db.add(record)
    db.commit()

    return UploadResponse(
        id=record.id,
        filename=record.filename,
        L=L,
        S=S,
        c=c,
        gsp_col=cell["col"],
        gsp_row=cell["row"],
        price=record.price,
        download_url=f"/api/v1/download/{record.id}"
    )

@app.get("/api/v1/files", response_model=List[FileSearchResult])
async def list_files(
    q: str = None,
    col: int = None,
    row: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(FileRecord)
    if q:
        query = query.filter(FileRecord.filename.ilike(f"%{q}%"))
    if col is not None and row is not None:
        query = query.filter(
            FileRecord.gsp_col == col,
            FileRecord.gsp_row == row
        )
    records = query.order_by(FileRecord.created_at.desc()).limit(100).all()
    return records

@app.get("/api/v1/download/{file_id}")
async def download_file(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    record.download_count += 1
    db.commit()

    return FileResponse(
        record.storage_path,
        media_type=record.content_type,
        filename=record.filename
    )