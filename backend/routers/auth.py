"""
DocSetu AI - Authentication Router
Handles user registration, login, and JWT token management.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from config import get_settings
from db import get_db
from models.database import User
from models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from services.email_service import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header.
        db: Database session.

    Returns:
        Authenticated User object.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        request: User registration data.
        db: Database session.

    Returns:
        Created user data.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # Create new user
    verification_token = secrets.token_urlsafe(32)

    # First registered user becomes admin automatically
    user_count = db.query(User).count()
    assigned_role = "admin" if user_count == 0 else "viewer"

    new_user = User(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        organization=request.organization,
        is_verified=False,
        verification_token=verification_token,
        role=assigned_role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (non-blocking, don't fail registration if email fails)
    await send_verification_email(
        email=new_user.email,
        token=verification_token,
        base_url=settings.app_base_url,
    )

    logger.info(f"New user registered: {new_user.email}")
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Args:
        request: Login credentials.
        db: Database session.

    Returns:
        JWT access token.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.id})

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user profile.

    Args:
        current_user: Authenticated user from JWT.

    Returns:
        User profile data.
    """
    return current_user



# --- Request models for new endpoints ---

class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# --- Email Verification & Password Reset Endpoints ---


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verify a user's email address using the token sent during registration.

    Args:
        request: Contains the verification token.
        db: Database session.

    Returns:
        Success message.
    """
    user = db.query(User).filter(User.verification_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    user.is_verified = True
    user.verification_token = None
    db.commit()

    logger.info(f"Email verified for user: {user.email}")
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiate password reset flow. Sends a reset link to the user's email.

    Args:
        request: Contains the user's email.
        db: Database session.

    Returns:
        Generic success message (doesn't reveal if email exists).
    """
    user = db.query(User).filter(User.email == request.email).first()

    if user:
        # Generate reset token with 1-hour expiration
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        # Send reset email
        await send_password_reset_email(
            email=user.email,
            token=reset_token,
            base_url=settings.app_base_url,
        )

        logger.info(f"Password reset requested for: {user.email}")

    # Always return success to prevent email enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset user's password using the token from the reset email.

    Args:
        request: Contains the reset token and new password.
        db: Database session.

    Returns:
        Success message.
    """
    user = db.query(User).filter(User.reset_token == request.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check token expiration
    if user.reset_token_expires is None or user.reset_token_expires < datetime.utcnow():
        # Clear expired token
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one.",
        )

    # Update password and clear reset token
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    logger.info(f"Password reset completed for: {user.email}")
    return {"message": "Password reset successfully"}
