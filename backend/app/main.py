import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from .database import Base, engine, get_db, SessionLocal
from .models import User, Complaint, Role, Status, Priority
from .schemas import RegisterIn, LoginIn, TokenOut, UserOut, ComplaintCreate, ComplaintUpdate, ComplaintOut
from .security import hash_password, verify_password, create_access_token, get_current_user, require_admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@campusfix.local").lower()
        admin = db.query(User).filter(func.lower(User.email) == admin_email).first()
        if not admin:
            db.add(User(name="CampusFix Admin", email=admin_email, password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "ChangeMe123!")), role=Role.admin, department="Facilities"))
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(title="CampusFix API", version="1.0.0", description="Campus maintenance and complaint management API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "campusfix-api"}

@app.post("/api/auth/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password), role=Role.student, department=payload.department)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user), "user": user}

@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user), "user": user}

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).filter(User.role.in_([Role.staff, Role.admin])).order_by(User.name).all()

@app.get("/api/complaints", response_model=list[ComplaintOut])
def list_complaints(status_filter: Status | None = Query(default=None, alias="status"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Complaint).options(joinedload(Complaint.reporter), joinedload(Complaint.assignee))
    if user.role == Role.student:
        query = query.filter(Complaint.reporter_id == user.id)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    return query.order_by(Complaint.created_at.desc()).all()

@app.post("/api/complaints", response_model=ComplaintOut, status_code=201)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    complaint = Complaint(**payload.model_dump(), reporter_id=user.id)
    db.add(complaint)
    db.commit()
    return db.query(Complaint).options(joinedload(Complaint.reporter), joinedload(Complaint.assignee)).filter(Complaint.id == complaint.id).first()

@app.patch("/api/complaints/{complaint_id}", response_model=ComplaintOut)
def update_complaint(complaint_id: int, payload: ComplaintUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    changes = payload.model_dump(exclude_unset=True)
    if "assigned_to_id" in changes and changes["assigned_to_id"] is not None:
        assignee = db.get(User, changes["assigned_to_id"])
        if not assignee or assignee.role not in [Role.staff, Role.admin]:
            raise HTTPException(status_code=400, detail="Select a valid staff member")
    for key, value in changes.items():
        setattr(complaint, key, value)
    complaint.updated_at = datetime.now(timezone.utc)
    db.commit()
    return db.query(Complaint).options(joinedload(Complaint.reporter), joinedload(Complaint.assignee)).filter(Complaint.id == complaint_id).first()

@app.get("/api/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = db.query(Complaint)
    if user.role == Role.student:
        base = base.filter(Complaint.reporter_id == user.id)
    total = base.count()
    counts = {s.value: base.filter(Complaint.status == s).count() for s in Status}
    urgent = base.filter(Complaint.priority == Priority.urgent, Complaint.status != Status.resolved).count()
    category_rows = base.with_entities(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    return {"total": total, "submitted": counts[Status.submitted.value], "in_progress": counts[Status.in_progress.value], "on_hold": counts[Status.on_hold.value], "resolved": counts[Status.resolved.value], "urgent": urgent, "resolution_rate": round(counts[Status.resolved.value] / total * 100) if total else 0, "categories": [{"name": name, "count": count} for name, count in category_rows]}
