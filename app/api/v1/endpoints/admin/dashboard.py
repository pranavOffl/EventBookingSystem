from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import RoleChecker, get_current_user
from app.db.models.user import User, Role
from app.db.async_session import get_db
from app.services.admin_service import admin_service
from app.schemas.admin import (
    AdminMessageResponse,
    AdminResponseBase,
    AdminEmailUpdateRequest,
    AdminPasswordUpdateRequest,
    AdminUpdate,
)

router = APIRouter()
role_checker = RoleChecker([Role.ADMIN])

@router.get("/details", response_model=AdminResponseBase, status_code=status.HTTP_200_OK)
async def get_admin_details(current_user: User = Depends(get_current_user), _: bool = Depends(role_checker)):
    """Get current admin details."""
        
    return AdminResponseBase(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role
    )

@router.patch("/update_email", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def update_admin_email(email_update: AdminEmailUpdateRequest, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Update admin email."""
    
    existing_user = await admin_service.get_user_by_email(session, email_update.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )

    # Convert to generic AdminUpdate for service layer
    update_data = AdminUpdate(email=email_update.email)
    
    updated_admin = await admin_service.update_admin(session, current_user, update_data)
    if not updated_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
        
    return AdminMessageResponse(message="Email updated successfully")

@router.patch("/update_password", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def update_admin_password(password_update: AdminPasswordUpdateRequest, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Update admin password."""
    
    if password_update.password != password_update.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )
    
    # Convert to generic AdminUpdate for service layer
    update_data = AdminUpdate(password=password_update.password)
    
    updated_admin = await admin_service.update_admin(session, current_user, update_data)
    if not updated_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
        
    return AdminMessageResponse(message="Password updated successfully")

@router.delete("/delete", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def delete_admin_account(current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Delete admin account."""
    
    deleted = await admin_service.delete_admin(session, current_user)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
        
    return AdminMessageResponse(message="Admin account deleted successfully")
