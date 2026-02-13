from datetime import datetime
from typing import List
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.db.models.booking import Booking
from app.db.models.event import Event
from app.db.models.user import User

class BookingService:
    async def create_booking(self, session: AsyncSession, user_id: UUID, event_id: UUID) -> Booking:
        # 2. Check Event Date & Capacity with Row Lock for Concurrency
        # We re-fetch the event with a lock to ensure accurate booked_seats count
        # This prevents race conditions where multiple users book the last seat simultaneously.
        statement = select(Event).where(Event.id == event_id).with_for_update()
        result = await session.exec(statement)
        event = result.one_or_none()
        
        if not event:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

        if event.date <= datetime.now(event.date.tzinfo):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book past events")

        if event.booked_seats >= event.capacity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is fully booked")

        # 4. Check for ANY Existing Booking (Active or Cancelled)
        statement = select(Booking).where(Booking.user_id == user_id, Booking.event_id == event_id)
        existing_booking = (await session.exec(statement)).first()
        
        if existing_booking:
            if existing_booking.status == "confirmed":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already booked this event")
            
            # If cancelled, reactivate it
            existing_booking.status = "confirmed"
            from datetime import timezone
            existing_booking.booking_date = datetime.now(timezone.utc) # Update timestamp to UTC
            new_booking = existing_booking
            session.add(new_booking)

        else:
            # 5. Create New Booking
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
