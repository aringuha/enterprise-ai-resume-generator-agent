import secrets
from typing import Annotated

import jwt
from fastapi import Header, HTTPException, status
from app.core.config import settings

def verify_jwt_token(token: str) -> bool:
    try:
        jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
        )
        return True
    except jwt.PyJWTError:
        return False

def verify_api_key(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> bool:
    bearer_token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.removeprefix("Bearer ").strip()

    valid_bearer = bearer_token and secrets.compare_digest(bearer_token, settings.bearer_token)
    valid_jwt = bearer_token and verify_jwt_token(bearer_token)
    valid_api_key = x_api_key and secrets.compare_digest(x_api_key, settings.api_key)

    if not (valid_bearer or valid_jwt or valid_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True
