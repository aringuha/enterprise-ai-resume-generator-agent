import pytest
import jwt
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import verify_api_key, verify_jwt_token


def test_verify_api_key_accepts_configured_key():
    assert verify_api_key(x_api_key=settings.api_key) is True


def test_verify_api_key_accepts_bearer_token():
    assert verify_api_key(authorization=f"Bearer {settings.bearer_token}") is True


def test_verify_api_key_accepts_signed_jwt():
    token = jwt.encode(
        {"sub": "test-user", "iss": settings.jwt_issuer},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    assert verify_api_key(authorization=f"Bearer {token}") is True


def test_verify_jwt_token_rejects_bad_issuer():
    token = jwt.encode(
        {"sub": "test-user", "iss": "wrong-issuer"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    assert verify_jwt_token(token) is False


def test_verify_api_key_rejects_invalid_key():
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(x_api_key="wrong-key")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or missing API credentials"
