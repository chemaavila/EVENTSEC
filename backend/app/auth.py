from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.handlers import bcrypt as passlib_bcrypt

try:  # pragma: no cover - runtime guard for bcrypt metadata changes
    import bcrypt  # type: ignore

    if not hasattr(bcrypt, "__about__"):
        class _BcryptAbout:
            __version__ = getattr(bcrypt, "__version__", "unknown")

        bcrypt.__about__ = _BcryptAbout()  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    bcrypt = None  # type: ignore


def _disable_passlib_wrap_check() -> None:
    """Passlib's wrap bug detector uses >72 byte secrets; coop with hardened bcrypt."""
    detect_fn = getattr(passlib_bcrypt, "detect_wrap_bug", None)
    if detect_fn:
        def _safe_detect_wrap_bug(*_args, **_kwargs):
            return False

        passlib_bcrypt.detect_wrap_bug = _safe_detect_wrap_bug  # type: ignore[attr-defined]


_disable_passlib_wrap_check()

from .schemas import UserProfile
from .config import settings

# Security configuration
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Initialize password context with explicit bcrypt backend
# Use lazy initialization to avoid bcrypt detection issues at import time
_pwd_context = None

def _get_pwd_context():
    """Lazy initialization of password context to avoid bcrypt detection issues."""
    global _pwd_context
    if _pwd_context is None:
        _pwd_context = CryptContext(
            schemes=["bcrypt"],
            bcrypt__rounds=12,
            deprecated="auto"
        )
    return _pwd_context

def _truncate_for_bcrypt(secret: str) -> str:
    if isinstance(secret, str):
        secret_bytes = secret.encode("utf-8")
        if len(secret_bytes) > 72:
            secret = secret_bytes[:72].decode("utf-8", errors="ignore")
    return secret


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _get_pwd_context().verify(_truncate_for_bcrypt(plain_password), hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return _get_pwd_context().hash(_truncate_for_bcrypt(password))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def _extract_token(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None),
) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if x_auth_token:
        return x_auth_token.strip()
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.strip()
    return None


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None),
) -> UserProfile:
    token = _extract_token(request, authorization, x_auth_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # This will be implemented in main.py
    from .main import users_db
    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None),
) -> Optional[UserProfile]:
    token = _extract_token(request, authorization, x_auth_token)
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        return None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    from .main import users_db

    return users_db.get(user_id)


async def get_current_admin_user(
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfile:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

