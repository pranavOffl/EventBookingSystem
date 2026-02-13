from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel
from uuid import UUID

from pydantic import field_validator

# Request Schemas
class EventBase(SQLModel):
    title: str
    description: str
    date: datetime
    location: str
    capacity: int

class EventCreateRequest(EventBase):
    @field_validator("date")
    def validate_date(cls, value):
        # Ensure value is timezone-aware for comparison
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if value <= now:
            raise ValueError("Event date must be in the future")
            
        # Return naive UTC datetime for DB compatibility
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @field_validator("capacity")
    def validate_capacity(cls, value):
        if value <= 0:
            raise ValueError("Capacity must be a positive number")
        return value

class EventUpdateRequest(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    capacity: Optional[int] = None

    @field_validator("date")
    def validate_date(cls, value):
        if value:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            if value <= now:
                raise ValueError("Event date must be in the future")
                
            # Return naive UTC datetime for DB compatibility
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @field_validator("capacity")
    def validate_capacity(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Capacity must be a positive number")
        return value

# Response Schemas
class EventResponseBase(EventBase):
    id: UUID
    booked_seats: int
    organizer_id: UUID

class EventMessageResponse(SQLModel):
    message: str

class EventCreateResponse(EventMessageResponse):
    event: EventResponseBase

class EventUpdateResponse(EventMessageResponse):
    event: EventResponseBase
