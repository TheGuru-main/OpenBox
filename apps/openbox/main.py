import os, shutil, uuid, hashlib
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from platform.models import Base, engine, SessionLocal, User, FileRecord, Message, Notification, Payment, Settings
from platform.schemas import *
from platform.gsp import user_placement, object_placement, name_length, digit_sum, first_letter_index

app = FastAPI(title="OpenBox", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Limits in bytes
LIMITS = {
    "app": 400 * 1024 * 1024,
    "game": 1.3 * 1024 * 1024 * 1024,  # 1.3 GB
    "video": 1.3 * 1024 * 1024 * 1024,
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user(x_user_phone: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not x_user_phone:
        raise HTTPException(401, "Missing user phone header")
    user = db.query(User).filter(User.phone == x_user_phone).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r") as f:
        return f.read()

# ---------- Auth ----------
@app.post("/api/v1/signup")
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(409, "Phone already registered")
    cell = user_placement(payload.full_name, payload.phone)
    user = User(
        phone=payload.phone,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        gsp_col=cell["col"],
        gsp_row=cell["row"],
    )
    db.add(user)
    db.commit()
    return {"message": "User created", "gsp_col": cell["col"], "gsp_row": cell["row"]}

@app.post("/api/v1/login")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or user.password_hash != hash_password(payload.password):
        raise HTTPException(401, "Invalid credentials")
    return {"message": "Login successful", "phone": user.phone}

# ---------- Upload / Files ----------
@app.post("/api/v1/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
    category: str = Form(...),
    price: float = Form(0.0),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if category not in LIMITS:
        raise HTTPException(400, "Invalid category. Must be app, game, or video")
    user = db.query(User).filter(User.phone == uploaded_by).first()
    if not user:
        raise HTTPException(404, "Uploader not registered")

    max_size = LIMITS[category]
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    storage_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    # Save with size limit
    size = 0
    with open(storage_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):   # 1MB chunks
            size += len(chunk)
            if size > max_size:
                buffer.close()
                os.remove(storage_path)
                raise HTTPException(413, f"File exceeds limit for {category}: {max_size//(1024*1024)} MB")
            buffer.write(chunk)

    # GSP placement
    cell = object_placement(file.filename)
    L = name_length(file.filename)
    S = digit_sum("550198550199")
    c = first_letter_index(file.filename)

    record = FileRecord(
        id=file_id,
        filename=file.filename,
        storage_path=storage_path,
        size_bytes=size,
        content_type=file.content_type,
        category=category,
        L=L, S=S, c=c,
        gsp_col=cell["col"],
        gsp_row=cell["row"],
        uploaded_by=uploaded_by,
        price=price,
        description=description,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return UploadResponse(
        id=record.id,
        filename=record.filename,
        category=record.category,
        gsp_col=record.gsp_col,
        gsp_row=record.gsp_row,
        price=record.price,
        download_url=f"/api/v1/download/{record.id}",
        created_at=record.created_at,
    )

@app.get("/api/v1/files", response_model=List[FileOut])
async def list_files(
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(FileRecord)
    if category:
        query = query.filter(FileRecord.category == category)
    if q:
        # Exact matches first, then closest
        exact = query.filter(FileRecord.filename.ilike(f"{q}")).all()
        fuzzy = query.filter(FileRecord.filename.ilike(f"%{q}%")).all()
        results = exact + [r for r in fuzzy if r not in exact]
        return results[:limit]
    return query.order_by(FileRecord.created_at.desc()).limit(limit).all()

@app.get("/api/v1/search")
async def search_files(
    q: str,
    category: Optional[str] = None,
    limit: int = 30,
    db: Session = Depends(get_db),
):
    if not q:
        raise HTTPException(400, "Query required")
    query = db.query(FileRecord)
    if category:
        query = query.filter(FileRecord.category == category)

    exact = query.filter(FileRecord.filename.ilike(f"{q}")).all()
    fuzzy = query.filter(FileRecord.filename.ilike(f"%{q}%")).all()
    # GSP similarity: objects with same first letter are likely related
    c = first_letter_index(q)
    same_letter = query.filter(FileRecord.c == c).all()

    results = []
    seen = set()
    for r in exact + fuzzy + same_letter:
        if r.id not in seen:
            results.append(r)
            seen.add(r.id)
        if len(results) >= limit:
            break
    return results

@app.get("/api/v1/download/{file_id}")
async def download_file(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(404, "File not found")
    record.download_count += 1
    db.commit()
    return FileResponse(record.storage_path, media_type=record.content_type, filename=record.filename)

@app.get("/api/v1/stream/{file_id}")
async def stream_file(file_id: str, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not record:
        raise HTTPException(404, "File not found")
    if not record.content_type.startswith("video/"):
        raise HTTPException(400, "Not a video file")
    def iterfile():
        with open(record.storage_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                yield chunk
    return StreamingResponse(iterfile(), media_type=record.content_type)

# ---------- Messages ----------
@app.post("/api/v1/messages", response_model=MessageOut)
async def send_message(payload: dict, db: Session = Depends(get_db)):
    from_phone = payload.get("from_phone")
    to_phone = payload.get("to_phone")
    body = payload.get("body", "")
    if not from_phone or not to_phone:
        raise HTTPException(400, "Missing from_phone or to_phone")
    msg = Message(from_phone=from_phone, to_phone=to_phone, body=body)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@app.get("/api/v1/messages", response_model=List[MessageOut])
async def get_messages(
    with_phone: str,
    user_phone: str = Header(...),
    db: Session = Depends(get_db),
):
    msgs = db.query(Message).filter(
        ((Message.from_phone == user_phone) & (Message.to_phone == with_phone)) |
        ((Message.from_phone == with_phone) & (Message.to_phone == user_phone))
    ).order_by(Message.created_at.asc()).all()
    return msgs

# ---------- My Posts ----------
@app.get("/api/v1/my-posts", response_model=List[FileOut])
async def my_posts(
    user_phone: str = Header(...),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(FileRecord).filter(FileRecord.uploaded_by == user_phone)
    if category:
        query = query.filter(FileRecord.category == category)
    return query.order_by(FileRecord.created_at.desc()).all()

@app.delete("/api/v1/my-posts/{file_id}")
async def delete_post(file_id: str, user_phone: str = Header(...), db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == file_id, FileRecord.uploaded_by == user_phone).first()
    if not record:
        raise HTTPException(404, "Post not found")
    if os.path.exists(record.storage_path):
        os.remove(record.storage_path)
    db.delete(record)
    db.commit()
    return {"ok": True}

# ---------- Notifications ----------
@app.get("/api/v1/notifications", response_model=List[NotificationOut])
async def get_notifications(user_phone: str = Header(...), db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_phone == user_phone).order_by(Notification.created_at.desc()).all()

@app.post("/api/v1/notifications/read")
async def mark_read(user_phone: str = Header(...), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_phone == user_phone, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"ok": True}

# ---------- Settings ----------
@app.get("/api/v1/settings")
async def get_settings(user_phone: str = Header(...), db: Session = Depends(get_db)):
    settings = db.query(Settings).filter(Settings.user_phone == user_phone).first()
    if not settings:
        settings = Settings(user_phone=user_phone)
        db.add(settings)
        db.commit()
    return settings

@app.put("/api/v1/settings")
async def update_settings(payload: dict, user_phone: str = Header(...), db: Session = Depends(get_db)):
    settings = db.query(Settings).filter(Settings.user_phone == user_phone).first()
    if not settings:
        settings = Settings(user_phone=user_phone)
        db.add(settings)
    if "language" in payload: settings.language = payload["language"]
    if "notifications_enabled" in payload: settings.notifications_enabled = payload["notifications_enabled"]
    if "theme" in payload: settings.theme = payload["theme"]
    db.commit()
    return settings

# ---------- Payments ----------
@app.post("/api/v1/payments/initiate")
async def initiate_payment(payload: dict, user_phone: str = Header(...), db: Session = Depends(get_db)):
    file_id = payload.get("file_id")
    amount = payload.get("amount")
    ref = str(uuid.uuid4())
    payment = Payment(user_phone=user_phone, file_id=file_id, amount=amount, reference=ref, status="pending")
    db.add(payment)
    db.commit()
    return {"reference": ref, "status": "pending"}

@app.post("/api/v1/payments/verify")
async def verify_payment(payload: dict, user_phone: str = Header(...), db: Session = Depends(get_db)):
    ref = payload.get("reference")
    payment = db.query(Payment).filter(Payment.reference == ref, Payment.user_phone == user_phone).first()
    if not payment:
        raise HTTPException(404, "Payment not found")
    payment.status = "paid"
    db.commit()
    return {"status": "paid"}

@app.get("/api/v1/payments/history")
async def payment_history(user_phone: str = Header(...), db: Session = Depends(get_db)):
    return db.query(Payment).filter(Payment.user_phone == user_phone).order_by(Payment.created_at.desc()).all()

# ---------- Premium ----------
@app.get("/api/v1/premium/status")
async def premium_status(user_phone: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == user_phone).first()
    return {"premium": user.premium if user else False}

@app.post("/api/v1/premium/subscribe")
async def subscribe_premium(user_phone: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == user_phone).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.premium = True
    db.commit()
    return {"premium": True}

@app.post("/api/v1/premium/cancel")
async def cancel_premium(user_phone: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == user_phone).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.premium = False
    db.commit()
    return {"premium": False}