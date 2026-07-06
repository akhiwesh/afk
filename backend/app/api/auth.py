from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from backend.app.core.settings import get_settings

settings = get_settings()
from typing import Optional

from backend.app.core.database import get_session
from backend.app.core.security import verify_password, create_access_token, get_password_hash
from backend.app.models.auth import User, Organization, UserRole
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < settings.min_password_length:
            raise ValueError(
                f"Password must be at least {settings.min_password_length} characters long"
            )
        if v.lower() == v or v.upper() == v or not any(c.isdigit() for c in v):
            raise ValueError(
                "Password must contain upper and lower case letters and at least one number"
            )
        return v

    @field_validator("full_name", "organization_name")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    organization_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", response_model=UserResponse)
def register(data: UserRegister, db: Session = Depends(get_session)):
    # Check if user already exists
    existing_user = db.exec(select(User).where(User.email == data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create Organization + Admin User in ONE transaction so a failure
    # cannot leave an orphaned organization behind.
    try:
        org = Organization(name=data.organization_name)
        db.add(org)
        db.flush()  # assigns org.id without committing

        new_user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=get_password_hash(data.password),
            role=UserRole.ADMIN,
            organization_id=org.id,
        )
        db.add(new_user)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(
    response: Response,
    data: LoginRequest,
    db: Session = Depends(get_session)
):
    user = db.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = create_access_token(subject=user.email)
    
    # Set HTTP-Only Cookie for seamless browser requests
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=3600 * 24 * 7,  # 7 days
        expires=3600 * 24 * 7,
        samesite="lax",
        secure=settings.is_production,  # HTTPS-only cookie in production
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": user.organization_id
        }
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    # In a real app, send password recovery email here
    return {"message": f"Password reset email sent to {data.email}"}
