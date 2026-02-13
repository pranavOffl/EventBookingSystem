from datetime import timedelta
from app.core.config import settings
from app.db.async_session import get_db
from app.core.redis import add_jti_to_blocklist
from app.services.admin_service import admin_service
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.utils import create_access_token
from app.schemas.admin import (
    AdminRequestBase,
    AdminResponseBase,
    AdminLoginResponse,
    AdminSignUpRequest,
    AdminSignUpResponse,
    AdminMessageResponse,
    AdminRefreshTokenResponse,
)
from app.core.security import access_token_bearer, refresh_token_bearer

router = APIRouter()

@router.post("/signup", response_model=AdminSignUpResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(admin_data: AdminSignUpRequest, session: AsyncSession = Depends(get_db)):
    """Create a new super admin user."""

    email = admin_data.email
    if admin_data.password != admin_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    user_exists = await admin_service.get_user_by_email(session, email)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User with email already exists",
        )

    new_admin = await admin_service.create_admin(session, admin_data)

    return AdminSignUpResponse(
        message="Admin created successfully",
        user=AdminResponseBase(
            id=new_admin.id,
            email=new_admin.email,
            role=new_admin.role
        )
    )

@router.post("/login", response_model=AdminLoginResponse, status_code=status.HTTP_200_OK)
async def login_admin(admin_data: AdminRequestBase, session: AsyncSession = Depends(get_db)):
    """Login admin user."""

    email = admin_data.email
    password = admin_data.password
    
    user = await admin_service.authenticate_admin(session, email, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
    access_token = create_access_token(user_data=user.model_dump(mode='json'), expiry=access_token_expires)
    
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRY)
    refresh_token = create_access_token(user_data=user.model_dump(mode='json'), expiry=refresh_token_expires, refresh=True)
    
    return AdminLoginResponse(
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        user=AdminResponseBase(
            id=user.id,
            email=user.email,
            role=user.role
        )
    )
    
@router.get("/refresh_token", response_model=AdminRefreshTokenResponse, status_code=status.HTTP_200_OK)
async def get_new_access_token(token_details: dict = Depends(refresh_token_bearer)):
    """Get new access token."""

    user = token_details["user"]

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
    new_access_token = create_access_token(user_data=user, expiry=access_token_expires)
    
    return AdminRefreshTokenResponse(
        message="Token refreshed successfully",
        access_token=new_access_token,
    )

@router.get("/logout", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def logout(token_details: dict = Depends(access_token_bearer)):
    """Logout admin user."""

    jti = token_details["jti"]

    await add_jti_to_blocklist(jti)

    return AdminMessageResponse(message="User logged out successfully")