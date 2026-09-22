from jose import JWTError, jwt

from app.core.config import get_settings


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        subject = payload.get("sub")
        return int(subject) if isinstance(subject, str) and subject.isdigit() else None
    except (JWTError, ValueError, TypeError):
        return None
