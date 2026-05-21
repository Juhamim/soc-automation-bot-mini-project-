from __future__ import annotations

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database.session import get_db
from app.database.crud import get_user_by_username
from app.database.models import User
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.config import settings

# This URL is what the swagger UI will hit to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def _system_user() -> User:
    """Minimal user object for API key auth (programmatic access)."""
    import uuid
    u = User(username="system", email="system@system", password_hash="", is_active=True)
    u.id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    return u


async def get_current_user_or_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User:
    """
    Accept either X-API-Key (programmatic) or Bearer JWT (dashboard).
    Matches README: API key for ingestion, JWT for dashboard.
    """
    if api_key:
        if api_key == settings.API_KEY:
            return _system_user()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
    if token:
        return await get_current_user(token=token, db=db)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
