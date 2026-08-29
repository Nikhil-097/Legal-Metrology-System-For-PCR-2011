import json
import os
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Shared In-Memory Rule Matrix Loader
_rule_matrix_cache: Optional[dict] = None

def get_rule_matrix() -> dict:
    """Loads and caches the codified Legal Metrology rules JSON."""
    global _rule_matrix_cache
    if _rule_matrix_cache is None:
        if not os.path.exists(settings.RULES_MATRIX_PATH):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rule matrix file missing at {settings.RULES_MATRIX_PATH}"
            )
        with open(settings.RULES_MATRIX_PATH, "r", encoding="utf-8") as f:
            _rule_matrix_cache = json.load(f)
    return _rule_matrix_cache

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validates JWT access token and returns user details."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "INSPECTOR")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except JWTError:
        raise credentials_exception