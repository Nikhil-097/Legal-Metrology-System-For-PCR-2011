from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel

from app.config import settings


router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str


# Prototype Mock Users
MOCK_USERS = {
    "officer@doca.gov.in": {
        "password": "password123",
        "role": "LEGAL_OFFICER",
    },
    "inspector@doca.gov.in": {
        "password": "password123",
        "role": "FIELD_INSPECTOR",
    },
}


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = MOCK_USERS.get(form_data.username)

    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": form_data.username,
            "role": user["role"],
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "username": form_data.username,
    }