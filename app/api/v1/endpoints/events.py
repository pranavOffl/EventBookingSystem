from typing import List, Optional
from fastapi import Query
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.rate_limiter import limiter
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.async_session import get_db
from app.db.models.user import User, Role
from app.core.security import get_current_user, RoleChecker
from app.services.event_service import event_service
from app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponseBase,
    EventCreateResponse,
    EventUpdateResponse,
    EventMessageResponse
)

router = APIRouter()
role_checker = RoleChecker([Role.ORGANIZER.value, Role.ADMIN.value])

@router.get("/", response_model=List[EventResponseBase], status_code=status.HTTP_200_OK)
async def list_events(
    session: AsyncSession = Depends(get_db), 
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100), 
    upcoming_only: bool = True
):
    """List all events (Public). Defaults to upcoming only. Supports pagination."""
    return await event_service.get_all_events(session, skip, limit, upcoming_only)

@router.get("/{event_id}", response_model=EventResponseBase, status_code=status.HTTP_200_OK)
async def get_event(event_id: UUID, session: AsyncSession = Depends(get_db)):
    """Get specific event details (Public)."""
    event = await event_service.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

@router.post("/", response_model=EventCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_event(request: Request, event_data: EventCreateRequest, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Create a new event (Organizer or Admin only)."""
        
    new_event = await event_service.create_event(session, event_data, current_user)
    
    return EventCreateResponse(
        message="Event created successfully",
        event=new_event
    )

@router.patch("/{event_id}", response_model=EventUpdateResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def update_event(request: Request, event_id: UUID, update_data: EventUpdateRequest, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Update event (Owner or Admin only)."""
    
    event = await event_service.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
    if current_user.role != Role.ADMIN.value and event.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to update this event")
        
    updated_event = await event_service.update_event(session, event, update_data)
    
    return EventUpdateResponse(
        message="Event updated successfully",
        event=updated_event
    )

@router.delete("/{event_id}", response_model=EventMessageResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def delete_event(request: Request, event_id: UUID, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker), session: AsyncSession = Depends(get_db)):
    """Delete event (Owner or Admin only)."""
    
    event = await event_service.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
    if current_user.role != Role.ADMIN.value and event.organizer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this event")
        
    await event_service.delete_event(session, event)
    
    return EventMessageResponse(message="Event deleted successfully")
