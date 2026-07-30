"""
DocSetu AI - Authentication Router
Handles user registration, login, JWT token management, and MFA.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from services.audit_service import AuditService
from services.mfa_service import MFAService
from utils.sanitizer import InputSanitizer

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
async def register(request: UserRegisterRequest, req: Request, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        request: User registration data.
        req: FastAPI Request object for IP extraction.
        db: Database session.

    Returns:
        Created user data.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

    # OWASP: Validate password strength
    is_valid, msg = InputSanitizer.validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    # OWASP: Sanitize inputs
    request.full_name = InputSanitizer.sanitize_string(request.full_name, 100)
    request.organization = InputSanitizer.sanitize_string(request.organization, 200) if request.organization else None

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

    # Audit log: registration
    await audit.log_event(
        event_type='auth.register',
        actor_id=new_user.id,
        actor_email=new_user.email,
        ip_address=ip_address,
        details={'role_assigned': assigned_role},
        resource_type='user',
        resource_id=new_user.id,
        status='success',
    )

    # Send verification email (non-blocking, don't fail registration if email fails)
    await send_verification_email(
        email=new_user.email,
        token=verification_token,
        base_url=settings.app_base_url,
    )

    logger.info(f"New user registered: {new_user.email}")
    return new_user


@router.post("/login")
async def login(request: UserLoginRequest, req: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    If MFA is enabled, returns a temporary MFA token instead.

    Args:
        request: Login credentials.
        req: FastAPI Request object for IP extraction.
        db: Database session.

    Returns:
        JWT access token or MFA challenge.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        # Audit log: login failure
        await audit.log_event(
            event_type='auth.login_failure',
            actor_id=user.id if user else None,
            actor_email=request.email,
            ip_address=ip_address,
            details={'reason': 'invalid_credentials'},
            status='failure',
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        # Audit log: login failure (deactivated)
        await audit.log_event(
            event_type='auth.login_failure',
            actor_id=user.id,
            actor_email=user.email,
            ip_address=ip_address,
            details={'reason': 'account_deactivated'},
            status='failure',
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # If MFA is enabled, return a temporary MFA token instead of the real access token
    if user.mfa_enabled:
        mfa_token = create_access_token(
            data={"sub": user.id, "type": "mfa_challenge"},
            expires_delta=timedelta(minutes=5),
        )

        # Audit log: MFA challenge issued
        await audit.log_event(
            event_type='auth.mfa_challenge',
            actor_id=user.id,
            actor_email=user.email,
            ip_address=ip_address,
            resource_type='user',
            resource_id=user.id,
            status='success',
        )

        logger.info(f"MFA challenge issued for: {user.email}")
        return {"requires_mfa": True, "mfa_token": mfa_token}

    # Create access token (no MFA)
    access_token = create_access_token(data={"sub": user.id})

    # Audit log: login success
    await audit.log_event(
        event_type='auth.login_success',
        actor_id=user.id,
        actor_email=user.email,
        ip_address=ip_address,
        resource_type='user',
        resource_id=user.id,
        status='success',
    )

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
async def forgot_password(request: ForgotPasswordRequest, req: Request, db: Session = Depends(get_db)):
    """
    Initiate password reset flow. Sends a reset link to the user's email.

    Args:
        request: Contains the user's email.
        req: FastAPI Request object for IP extraction.
        db: Database session.

    Returns:
        Generic success message (doesn't reveal if email exists).
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

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

    # Audit log: password reset request
    await audit.log_event(
        event_type='auth.password_reset_request',
        actor_id=user.id if user else None,
        actor_email=request.email,
        ip_address=ip_address,
        resource_type='user',
        resource_id=user.id if user else None,
        status='success',
    )

    # Always return success to prevent email enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, req: Request, db: Session = Depends(get_db)):
    """
    Reset user's password using the token from the reset email.

    Args:
        request: Contains the reset token and new password.
        req: FastAPI Request object for IP extraction.
        db: Database session.

    Returns:
        Success message.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

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

    # Audit log: password reset success
    await audit.log_event(
        event_type='auth.password_reset_success',
        actor_id=user.id,
        actor_email=user.email,
        ip_address=ip_address,
        resource_type='user',
        resource_id=user.id,
        status='success',
    )

    logger.info(f"Password reset completed for: {user.email}")
    return {"message": "Password reset successfully"}


# ==================== MFA Endpoints ====================


class MFATokenRequest(BaseModel):
    """Schema for MFA token verification."""
    token: str


class MFALoginRequest(BaseModel):
    """Schema for completing MFA login."""
    mfa_token: str
    totp_code: str


class MFASetupResponse(BaseModel):
    """Schema for MFA setup response."""
    secret: str
    qr_code_base64: str
    uri: str


class MFAVerifySetupResponse(BaseModel):
    """Schema for MFA verify setup response."""
    enabled: bool
    message: str


class MFADisableResponse(BaseModel):
    """Schema for MFA disable response."""
    enabled: bool


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate MFA secret and QR code for setup.
    Requires authentication. Admin only.

    Args:
        req: FastAPI Request object for IP extraction.
        current_user: Authenticated admin user.
        db: Database session.

    Returns:
        MFA secret, QR code (base64 PNG), and provisioning URI.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

    # Admin only
    if not current_user.is_admin and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA setup is only available for admin accounts",
        )

    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled. Disable it first to reconfigure.",
        )

    # Generate new secret
    secret = MFAService.generate_secret()

    # Store secret (not yet enabled - user must verify first)
    current_user.mfa_secret = secret
    db.commit()

    # Generate provisioning URI and QR code
    uri = MFAService.get_totp_uri(secret, current_user.email)
    qr_code_base64 = MFAService.generate_qr_code(uri)

    # Audit log
    await audit.log_event(
        event_type='auth.mfa_setup_initiated',
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=ip_address,
        resource_type='user',
        resource_id=current_user.id,
        status='success',
    )

    logger.info(f"MFA setup initiated for: {current_user.email}")
    return MFASetupResponse(secret=secret, qr_code_base64=qr_code_base64, uri=uri)


@router.post("/mfa/verify-setup", response_model=MFAVerifySetupResponse)
async def mfa_verify_setup(
    request: MFATokenRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify the first TOTP code to activate MFA.
    User must provide a valid TOTP token from their authenticator app.

    Args:
        request: Contains the TOTP token to verify.
        req: FastAPI Request object for IP extraction.
        current_user: Authenticated admin user.
        db: Database session.

    Returns:
        Confirmation that MFA is now enabled.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup has not been initiated. Call /mfa/setup first.",
        )

    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled.",
        )

    # Verify the TOTP token
    if not MFAService.verify_totp(current_user.mfa_secret, request.token):
        # Audit log: MFA setup verification failed
        await audit.log_event(
            event_type='auth.mfa_setup_verify_failure',
            actor_id=current_user.id,
            actor_email=current_user.email,
            ip_address=ip_address,
            details={'reason': 'invalid_totp_token'},
            resource_type='user',
            resource_id=current_user.id,
            status='failure',
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Please try again.",
        )

    # Enable MFA
    current_user.mfa_enabled = True
    db.commit()

    # Audit log: MFA enabled
    await audit.log_event(
        event_type='auth.mfa_enabled',
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=ip_address,
        resource_type='user',
        resource_id=current_user.id,
        status='success',
    )

    logger.info(f"MFA enabled for: {current_user.email}")
    return MFAVerifySetupResponse(enabled=True, message="MFA has been successfully enabled.")


@router.post("/mfa/disable", response_model=MFADisableResponse)
async def mfa_disable(
    request: MFATokenRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disable MFA for the current user.
    Requires a valid TOTP code to confirm.

    Args:
        request: Contains the TOTP token to confirm identity.
        req: FastAPI Request object for IP extraction.
        current_user: Authenticated admin user.
        db: Database session.

    Returns:
        Confirmation that MFA is disabled.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not currently enabled.",
        )

    # Verify the TOTP token before disabling
    if not MFAService.verify_totp(current_user.mfa_secret, request.token):
        # Audit log: MFA disable failed
        await audit.log_event(
            event_type='auth.mfa_disable_failure',
            actor_id=current_user.id,
            actor_email=current_user.email,
            ip_address=ip_address,
            details={'reason': 'invalid_totp_token'},
            resource_type='user',
            resource_id=current_user.id,
            status='failure',
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Cannot disable MFA.",
        )

    # Disable MFA and clear secret
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()

    # Audit log: MFA disabled
    await audit.log_event(
        event_type='auth.mfa_disabled',
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=ip_address,
        resource_type='user',
        resource_id=current_user.id,
        status='success',
    )

    logger.info(f"MFA disabled for: {current_user.email}")
    return MFADisableResponse(enabled=False)


@router.post("/mfa/login", response_model=TokenResponse)
async def mfa_login(request: MFALoginRequest, req: Request, db: Session = Depends(get_db)):
    """
    Complete login with TOTP code after MFA challenge.
    Validates the temporary MFA token and TOTP code, then issues the real access token.

    Args:
        request: Contains the temporary mfa_token and totp_code.
        req: FastAPI Request object for IP extraction.
        db: Database session.

    Returns:
        Full JWT access token upon successful MFA verification.
    """
    audit = AuditService(db)
    ip_address = req.client.host if req.client else None

    # Validate the temporary MFA token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired MFA token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            request.mfa_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "mfa_challenge":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.mfa_enabled or not user.mfa_secret:
        raise credentials_exception

    # Verify the TOTP code
    if not MFAService.verify_totp(user.mfa_secret, request.totp_code):
        # Audit log: MFA login failure
        await audit.log_event(
            event_type='auth.mfa_login_failure',
            actor_id=user.id,
            actor_email=user.email,
            ip_address=ip_address,
            details={'reason': 'invalid_totp_code'},
            resource_type='user',
            resource_id=user.id,
            status='failure',
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue the real access token
    access_token = create_access_token(data={"sub": user.id})

    # Audit log: login success (after MFA)
    await audit.log_event(
        event_type='auth.login_success',
        actor_id=user.id,
        actor_email=user.email,
        ip_address=ip_address,
        details={'mfa_verified': True},
        resource_type='user',
        resource_id=user.id,
        status='success',
    )

    logger.info(f"MFA login completed for: {user.email}")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
