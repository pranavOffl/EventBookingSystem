from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.async_session import get_db
from app.core.security import get_current_user
from app.db.models.user import User

from app.services.user_service import user_service
from app.schemas.user import (
    UserResponseBase,
    UserMessageResponse,
    UserUpdate,
    UserEmailUpdateRequest,
    UserPasswordUpdateRequest,
    UserRoleUpdateRequest
)

router = APIRouter()

@router.get("/details", response_model=UserResponseBase, status_code=status.HTTP_200_OK)
async def get_user_details(current_user: User = Depends(get_current_user)):
    """Get current user details."""
    
    return UserResponseBase(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role
    )

@router.patch("/update-email", response_model=UserMessageResponse, status_code=status.HTTP_200_OK)
async def update_user_email(email_update: UserEmailUpdateRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """
    Update authentication email for current user.
    """
    
    user_exists = await user_service.get_user_by_email(session, email_update.email)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )
        
    update_data = UserUpdate(email=email_update.email)
    
    updated_user = await user_service.update_user(session, current_user, update_data)
    
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return UserMessageResponse(message="Email updated successfully")

@router.patch("/update-password", response_model=UserMessageResponse, status_code=status.HTTP_200_OK)
async def update_user_password(password_update: UserPasswordUpdateRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """
    Update password for the currently logged-in user.
    Does NOT require current password.
    """
    
    if password_update.password != password_update.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
        
    update_data = UserUpdate(
        password=password_update.password,
        confirm_password=password_update.confirm_password
    )
    
    updated_user = await user_service.update_user(session, current_user, update_data)
    
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return UserMessageResponse(message="Password updated successfully")

@router.patch("/update-role", response_model=UserMessageResponse, status_code=status.HTTP_200_OK)
async def update_user_role(role_update: UserRoleUpdateRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """
    Update role for the currently logged-in user (Organizer <-> Attendee).
    """
    
    # We rely on the schema UserRoleUpdateRequest which uses UserSignUpRole Enum
    # This prevents users from setting themselves as 'admin' as it's not in that Enum.
    
    update_data = UserUpdate(role=role_update.role)
    
    updated_user = await user_service.update_user(session, current_user, update_data)
    
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return UserMessageResponse(message="Role updated successfully")

@router.delete("/delete", response_model=UserMessageResponse, status_code=status.HTTP_200_OK)
async def delete_user_account(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """Delete current user account."""
    
    # We might want to remove this or make it logically soft delete later
    # For now, it physically deletes.
    await session.delete(current_user)
    await session.commit()
    
    return UserMessageResponse(message="User account deleted successfully")
