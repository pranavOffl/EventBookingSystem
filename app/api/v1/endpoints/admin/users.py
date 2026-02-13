from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.async_session import get_db
from app.db.models.user import User, Role
from app.core.security import get_current_user, RoleChecker
from app.services.admin_service import admin_service
from app.schemas.admin import (
    UserWithStats,
    UserDetailResponse,
    UserRoleUpdateAdmin,
    AdminMessageResponse
)

router = APIRouter()
role_checker = RoleChecker([Role.ADMIN.value])

@router.get("/attendees", response_model=List[UserWithStats], status_code=status.HTTP_200_OK)
async def list_attendees(current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """List all users with role 'attendee' and their booking counts."""
    results = await admin_service.list_attendees(session)
    return [
        UserWithStats(
            id=u.id, 
            email=u.email, 
            role=u.role, 
            booking_count=cnt, 
            event_count=0
        ) for u, cnt in results
    ]

@router.get("/organizers", response_model=List[UserWithStats], status_code=status.HTTP_200_OK)
async def list_organizers(current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """List all users with role 'organizer' and their hosted event counts."""
    results = await admin_service.list_organizers(session)
    return [
        UserWithStats(
            id=u.id, 
            email=u.email, 
            role=u.role, 
            booking_count=0, 
            event_count=cnt
        ) for u, cnt in results
    ]

@router.get("/details/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def get_user_details(user_id: UUID, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Get full details of a specific user (bookings, events)."""
    user, b_cnt, e_cnt, bookings, events = await admin_service.get_user_stats(session, user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        booking_count=b_cnt,
        event_count=e_cnt,
        bookings=bookings,
        events=events
    )

@router.patch("/role/{user_id}", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def update_user_role(user_id: UUID, role_update: UserRoleUpdateAdmin, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Change a specific user's role (promote/demote)."""
    user = await admin_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    if role_update.role not in [r.value for r in Role]:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    updated_user = await admin_service.update_user_role(session, user, role_update.role)
    return AdminMessageResponse(message=f"User role updated to {updated_user.role}")

@router.delete("/{user_id}", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def delete_user(user_id: UUID, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Ban or delete a specific user account."""
    user = await admin_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    if user.id == current_user.id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account via user management")

    await admin_service.delete_admin(session, user)
    return AdminMessageResponse(message="User account deleted successfully")
