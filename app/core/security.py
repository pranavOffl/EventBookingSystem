from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from app.core.utils import decode_token
from app.db.models.user import User
from app.db.async_session import get_db
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Any, Dict
from fastapi import HTTPException, Request, status, Depends
from app.core.redis import token_in_blocklist

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        creds = await super().__call__(request)

        token = creds.credentials
        token_data = decode_token(token)

        if not self.token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail={
                    "error":"This token is invalid or expired",
                    "resolution":"Please get new token"
                }
            )

        # Check if token is revoked
        if await token_in_blocklist(token_data['jti']):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail={
                    "error":"This token has been invalid or revoked",
                    "resolution":"Please get new token"
                }
            )

        self.verify_token_data(token_data)

        return token_data

    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)
        return token_data is not None 

    def verify_token_data(self, token_data):
        raise NotImplementedError("Please Override this method in child classes")

class AccessTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide an access token",
            )

access_token_bearer = AccessTokenBearer()

class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self, token_data: dict) -> None:
        if token_data and not token_data["refresh"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please provide a refresh token",
            )

refresh_token_bearer = RefreshTokenBearer()

async def get_current_user(token_details: Dict = Depends(access_token_bearer), session: AsyncSession = Depends(get_db)) -> User:
    user = await session.get(User, token_details["user"]["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> Any:
        if current_user.role in self.allowed_roles:
            return True

        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to perform this action."
        )