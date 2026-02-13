from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from app.db.models.booking import Booking
from app.db.models.event import Event
from app.db.models.user import User

class BookingService:
    async def create_booking(self, session: AsyncSession, user_id: UUID, event_id: UUID) -> Booking:
        # 1. Fetch Event
        event = await session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        # 2. Check Event Date
        if event.date <= datetime.now(event.date.tzinfo):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book past events")
             
        # 3. Check Capacity
        # Lock row for update to prevent race condition? Or check simply.
        # Simple check for now.
        if event.booked_seats >= event.capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is fully booked")

        # 4. Check Existing Booking
        statement = select(Booking).where(Booking.user_id == user_id, Booking.event_id == event_id, Booking.status == "confirmed")
        existing_booking = await session.exec(statement)
        if existing_booking.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already booked this event")

        # 5. Create Booking
        new_booking = Booking(user_id=user_id, event_id=event_id, status="confirmed")
        session.add(new_booking)
        
        # 6. Update Event Seats
        event.booked_seats += 1
        session.add(event)
        
        await session.commit()
        await session.refresh(new_booking)
        return new_booking

    async def get_user_bookings(self, session: AsyncSession, user_id: UUID) -> List[Booking]:
        statement = select(Booking).where(Booking.user_id == user_id).order_by(Booking.booking_date.desc())
        result = await session.exec(statement)
        return result.all()

    async def cancel_booking(self, session: AsyncSession, booking_id: UUID, current_user: User) -> Booking:
    
        booking = await session.get(Booking, booking_id)
             
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        # Allow if user owns the booking OR user is an admin
        if booking.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this booking")

        if booking.status == "cancelled":
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is already cancelled")
             
        # Update Status
        booking.status = "cancelled"
        session.add(booking)
        
        # Update Event Seats
        event = await session.get(Event, booking.event_id)
        if event:
            event.booked_seats = max(0, event.booked_seats - 1)
            session.add(event)
            
        await session.commit()
        await session.refresh(booking)
        return booking

    async def get_event_attendees(self, session: AsyncSession, event_id: UUID) -> List[User]:
        # Join Booking and User
        statement = select(User).join(Booking).where(Booking.event_id == event_id, Booking.status == "confirmed")
        result = await session.exec(statement)
        return result.all()

booking_service = BookingService()
