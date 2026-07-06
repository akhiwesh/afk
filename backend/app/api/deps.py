from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session, select
from backend.app.core.database import get_session
from backend.app.core.security import decode_access_token
from backend.app.models.auth import User, UserRole

# Standard OAuth2 scheme (reads from Authorization header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

def get_token_from_header_or_cookie(request: Request, token: str = Depends(oauth2_scheme)) -> str:
    # 1. Check header first
    if token:
        return token
    # 2. Check Cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # If stored as 'Bearer <token>'
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:]
        return cookie_token
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Access token missing.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(
    db: Session = Depends(get_session),
    token: str = Depends(get_token_from_header_or_cookie)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.exec(select(User).where(User.email == user_email)).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user

# Helper dependencies
get_admin_user = RoleChecker([UserRole.ADMIN])
get_team_user = RoleChecker([UserRole.ADMIN, UserRole.TEAM])
