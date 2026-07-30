"""
DocSetu AI - Lambda Main (DynamoDB version)
Lightweight FastAPI app for AWS Lambda with DynamoDB backend.
"""

import os
import uuid
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, status, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from config import get_settings

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App ---
app = FastAPI(title="DocSetu AI", version="v1", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Utils ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# --- DynamoDB ---
from db_dynamo import DynamoUser, DynamoDocument


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=401, detail="Invalid credentials")
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = DynamoUser.get_by_id(user_id)
    if not user:
        raise credentials_exception
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")
    return user


# --- Schemas ---
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str = ""
    organization: str = ""

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# --- Health ---
@app.get("/health")
async def health():
    return {"status": "healthy", "app_name": "DocSetu AI", "version": "v1",
            "environment": "production", "database": "dynamodb",
            "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"app": "DocSetu AI", "description": "AI Document Intelligence Platform for India",
            "version": "v1", "docs": "/docs", "health": "/health",
            "endpoints": {"auth": "/api/auth", "documents": "/api/documents",
                         "compliance": "/api/compliance", "payments": "/api/payments"}}


# --- Auth ---
@app.post("/api/auth/register", status_code=201)
async def register(req: RegisterRequest):
    if DynamoUser.get_by_email(req.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    if DynamoUser.get_by_username(req.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    # First user gets admin role
    role = "admin" if DynamoUser.count_all() == 0 else "viewer"
    hashed = pwd_context.hash(req.password)
    user = DynamoUser.create(
        email=req.email, username=req.username, hashed_password=hashed,
        full_name=req.full_name, organization=req.organization, role=role,
    )
    return {"id": user["id"], "email": user["email"], "username": user["username"],
            "full_name": user["full_name"], "organization": user["organization"],
            "is_active": True, "created_at": user["created_at"]}


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = DynamoUser.get_by_email(req.email)
    if not user or not pwd_context.verify(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")
    token = create_access_token(data={"sub": user["id"]})
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


@app.get("/api/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "username": user["username"],
            "full_name": user.get("full_name", ""), "organization": user.get("organization", ""),
            "role": user.get("role", "viewer"), "is_active": user.get("is_active", True),
            "created_at": user.get("created_at")}


# --- Documents ---
@app.post("/api/documents/upload", status_code=202)
async def upload_document(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ["pdf", "png", "jpg", "jpeg", "tiff", "bmp"]:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 50MB limit")

    # Save to /tmp (Lambda) - in production would go to S3
    doc_id = str(uuid.uuid4())
    file_path = f"/tmp/uploads/{doc_id}.{ext}"
    os.makedirs("/tmp/uploads", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    doc = DynamoDocument.create(
        filename=f"{doc_id}.{ext}", original_filename=file.filename,
        file_path=file_path, file_type=ext, file_size=len(content),
        mime_type=file.content_type or "", owner_id=user["id"],
    )
    return {"id": doc["id"], "filename": file.filename, "status": "uploaded",
            "message": "Document uploaded successfully. Processing queued."}


@app.get("/api/documents/")
async def list_documents(page: int = 1, page_size: int = 20, user=Depends(get_current_user)):
    docs = DynamoDocument.get_by_owner(user["id"], limit=page_size)
    total = DynamoDocument.count_by_owner(user["id"])
    return {"documents": docs, "total": total, "page": page,
            "page_size": page_size, "total_pages": (total + page_size - 1) // page_size if total > 0 else 0}


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, user=Depends(get_current_user)):
    doc = DynamoDocument.get_by_id(doc_id)
    if not doc or doc.get("owner_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.delete("/api/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: str, user=Depends(get_current_user)):
    doc = DynamoDocument.get_by_id(doc_id)
    if not doc or doc.get("owner_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Document not found")
    DynamoDocument.delete(doc_id)


# --- Compliance ---
@app.get("/api/compliance/rules")
async def get_compliance_rules(user=Depends(get_current_user)):
    from services.compliance_engine import COMPLIANCE_RULES
    return {"rules": COMPLIANCE_RULES, "total": len(COMPLIANCE_RULES),
            "categories": list(set(r["category"] for r in COMPLIANCE_RULES))}


# --- Payments ---
PLANS = [
    {"id": "free", "name": "Free", "price": 0, "docs_per_month": 10, "features": ["Basic OCR", "2 languages"]},
    {"id": "starter", "name": "Starter", "price": 299900, "docs_per_month": 500, "features": ["5 languages", "Compliance", "Email support"]},
    {"id": "business", "name": "Business", "price": 1499900, "docs_per_month": 5000, "features": ["All languages", "Autopilot", "Priority support"]},
    {"id": "enterprise", "name": "Enterprise", "price": 0, "docs_per_month": -1, "features": ["Custom", "Dedicated AM"]},
]

@app.get("/api/payments/plans")
async def get_plans():
    return {"plans": PLANS}


# --- Admin ---
@app.get("/api/admin/stats")
async def get_stats(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return {"total_users": DynamoUser.count_all(),
            "total_documents": DynamoDocument.count_all()}
