from typing import List, Optional
from sqlalchemy import or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from app.db.models.event import Event
from app.db.models.user import User
from app.schemas.event import EventCreateRequest, EventUpdateRequest

class EventService:
    async def get_event_by_id(self, session: AsyncSession, event_id: UUID) -> Optional[Event]:
        return await session.get(Event, event_id)
        
    async def get_all_events(self, session: AsyncSession, skip: int = 0, limit: int = 20, upcoming_only: bool = True) -> List[Event]:
        statement = select(Event)
        if upcoming_only:
            # Use naive UTC time for comparison because DB stores naive timestamps
            statement = statement.where(Event.date > datetime.utcnow())
        statement = statement.offset(skip).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def search_events(self, session: AsyncSession, query: Optional[str] = None, location: Optional[str] = None, date_start: Optional[datetime] = None, date_end: Optional[datetime] = None, upcoming_only: bool = True, limit: int = 20) -> List[Event]:
        statement = select(Event)
        
        # Default to upcoming only unless specific dates are requested
        if upcoming_only and not date_start and not date_end:
            statement = statement.where(Event.date > datetime.utcnow())
            
        if date_start:
            statement = statement.where(Event.date >= date_start)
            
        if date_end:
             statement = statement.where(Event.date <= date_end)
             
        if query:
            statement = statement.where(
                or_(
                    Event.title.ilike(f"%{query}%"),
                    Event.description.ilike(f"%{query}%")
                )
            )
            
        if location:
            statement = statement.where(Event.location.ilike(f"%{location}%"))
            
        statement = statement.limit(limit)
        statement = statement.order_by(Event.date)
        result = await session.exec(statement)
        return result.all()
    
    async def create_event(self, session: AsyncSession, event_data: EventCreateRequest, organizer: User) -> Event:
        # Check for duplicate event by the same organizer
        existing_event = await session.exec(
            select(Event).where(
                Event.title == event_data.title,
                Event.date == event_data.date,
                Event.location == event_data.location,
                Event.organizer_id == organizer.id
            )
        )
        if existing_event.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already created an event with this title, date, and location."
            )

        new_event = Event(
            title=event_data.title,
            description=event_data.description,
            date=event_data.date,
            location=event_data.location,
            capacity=event_data.capacity,
            organizer_id=organizer.id,
            booked_seats=0
        )
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)
        return new_event
        
    async def update_event(self, session: AsyncSession, event: Event, update_data: EventUpdateRequest) -> Event:
        event_data = update_data.model_dump(exclude_unset=True)
        for key, value in event_data.items():
            setattr(event, key, value)
            
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    async def delete_event(self, session: AsyncSession, event: Event):
        await session.delete(event)
        await session.commit()

event_service = EventService()
