"""FastAPI dependencies: auth, DB session."""

from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.models.user import User, UserRole

security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_token: str | None = Cookie(default=None, alias="access_token"),
) -> str | None:
    """Extract user id from JWT (Authorization header or HTTP-only cookie)."""
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token
    if not token:
        return None
    return decode_access_token(token)


def get_current_user_required(
    user_id: str | None = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
) -> User:
    """Require valid JWT; return User or 401."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_chief_doctor_required(
    user: User = Depends(get_current_user_required),
) -> User:
    """Require Chief Doctor role; return User or 403."""
    if user.role != UserRole.CHIEF_DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chief Doctor access required",
        )
    return user
