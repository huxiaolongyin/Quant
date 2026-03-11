from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[dict] = None,
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=Settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"sub": str(subject), "exp": expire, "type": "access"}
    if extra_data:
        to_encode.update(extra_data)

    encoded_jwt = jwt.encode(
        to_encode, Settings.JWT_SECRET_KEY, algorithm=Settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=Settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {"sub": str(subject), "exp": expire, "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, Settings.JWT_SECRET_KEY, algorithm=Settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, Settings.JWT_SECRET_KEY, algorithms=[Settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != token_type:
        return None
    return payload.get("sub")