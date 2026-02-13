from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.rate_limiter import limiter
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.async_session import get_db
from app.db.models.user import User, Role
from app.core.security import get_current_user, RoleChecker
from app.services.booking_service import booking_service
from app.services.event_service import event_service
from app.schemas.booking import (
    BookingCreate,
    BookingRead,
    BookingMessageResponse
)
from app.schemas.user import UserResponseBase

router = APIRouter()
role_checker_organizer = RoleChecker([Role.ORGANIZER.value, Role.ADMIN.value])
role_checker_attendee = RoleChecker([Role.ATTENDEE.value, Role.ADMIN.value])

@router.post("/", response_model=BookingMessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_booking(request: Request, booking_data: BookingCreate, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker_attendee), session: AsyncSession = Depends(get_db)):
    """Book a ticket for an event"""
    booking = await booking_service.create_booking(session, current_user.id, booking_data.event_id)
    return BookingMessageResponse(message="Booking created successfully", booking=booking)

@router.get("/my-bookings", response_model=List[BookingRead], status_code=status.HTTP_200_OK)
async def get_my_bookings(current_user: User = Depends(get_current_user), _: bool = Depends(role_checker_attendee), session: AsyncSession = Depends(get_db)):
    """List all events currently booked by the logged-in user"""
    return await booking_service.get_user_bookings(session, current_user.id)

@router.delete("/{booking_id}", response_model=BookingMessageResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def cancel_booking(request: Request, booking_id: UUID, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker_attendee), session: AsyncSession = Depends(get_db)):
    """Cancel a booking"""
    cancelled_booking = await booking_service.cancel_booking(session, booking_id, current_user)
    return BookingMessageResponse(message="Booking cancelled successfully", booking=cancelled_booking)

@router.get("/{event_id}", response_model=List[UserResponseBase], status_code=status.HTTP_200_OK)
async def get_event_attendees(event_id: UUID, current_user: User = Depends(get_current_user), _: bool = Depends(role_checker_organizer), session: AsyncSession = Depends(get_db)):
    """List all attendees for a specific event (Guest List)"""
    event = await event_service.get_event_by_id(session, event_id)
    if not event:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
         
    if current_user.role != Role.ADMIN.value and event.organizer_id != current_user.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view guest list for this event")

    attendees = await booking_service.get_event_attendees(session, event_id)
    return [UserResponseBase(id=u.id, email=u.email, role=u.role) for u in attendees]
