from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.async_session import get_db
from app.core.config import settings
from app.core.redis import add_jti_to_blocklist
from app.core.utils import create_access_token
from app.core.security import access_token_bearer, refresh_token_bearer

from app.services.user_service import user_service
from app.schemas.user import (
    UserRequestBase,
    UserSignUpRequest,
    UserSignUpResponse,
    UserLoginResponse,
    UserRefreshTokenResponse,
    UserMessageResponse,
    UserResponseBase
)

router = APIRouter()

@router.post("/signup", response_model=UserSignUpResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserSignUpRequest, session: AsyncSession = Depends(get_db)):
    """Create a new user (Attendee or Organizer)."""
    
    email = user_data.email
    
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
        
    user_exists = await user_service.get_user_by_email(session, email)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User with email already exists"
        )
        
    new_user = await user_service.create_user(session, user_data)
    
    return UserSignUpResponse(
        message="User created successfully",
        user=UserResponseBase(
            id=new_user.id,
            email=new_user.email,
            role=new_user.role
        )
    )

@router.post("/login", response_model=UserLoginResponse, status_code=status.HTTP_200_OK)
async def login_user(user_data: UserRequestBase, session: AsyncSession = Depends(get_db)):
    """Login user."""
    
    email = user_data.email
    password = user_data.password
    
    user = await user_service.authenticate_user(session, email, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
    access_token = create_access_token(
        user_data={"id": str(user.id), "email": user.email, "role": user.role}, 
        expiry=access_token_expires
    )
    
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRY)
    refresh_token = create_access_token(
        user_data={"id": str(user.id), "email": user.email, "role": user.role}, 
        expiry=refresh_token_expires, 
        refresh=True
    )
    
    return UserLoginResponse(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponseBase(
            id=user.id,
            email=user.email,
            role=user.role
        )
    )

@router.get("/refresh_token", response_model=UserRefreshTokenResponse, status_code=status.HTTP_200_OK)
async def get_new_access_token(token_details: dict = Depends(refresh_token_bearer)):
    """Get new access token."""
    
    user_data = token_details["user"]
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
    new_access_token = create_access_token(user_data=user_data, expiry=access_token_expires)
    
    return UserRefreshTokenResponse(
        message="Token refreshed successfully",
        access_token=new_access_token
    )
    
@router.get("/logout", response_model=UserMessageResponse, status_code=status.HTTP_200_OK)
async def logout(token_details: dict = Depends(access_token_bearer)):
    """Logout user."""
    
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    
    return UserMessageResponse(message="User logged out successfully")