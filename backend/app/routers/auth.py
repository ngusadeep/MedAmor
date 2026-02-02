"""Auth API: login (JWT), optional logout."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.deps import get_current_user_required
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Default demo user if DB has no users (create on first request or via seed)
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo"  # Change in production


def _ensure_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.username == DEMO_USERNAME).first()
    if not user:
        user = User(
            username=DEMO_USERNAME,
            hashed_password=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db_session),
):
    """Login with username/password. Returns JWT and sets HTTP-only cookie."""
    user = db.query(User).filter(User.username == body.username).first()
    if not user:
        if body.username == DEMO_USERNAME and body.password == DEMO_PASSWORD:
            user = _ensure_demo_user(db)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
    else:
        if not verify_password(body.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
    token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600 * 24,
    )
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(response: Response):
    """Clear access_token cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user_required)):
    """Return current user from JWT (Bearer or cookie)."""
    return UserResponse(id=str(user.id), username=user.username)
