from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel
from uuid import UUID

from pydantic import field_validator, Field

# Request Schemas
class EventBase(SQLModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(max_length=1000)
    date: datetime
    location: str = Field(min_length=3, max_length=200)
    capacity: int = Field(gt=0)

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
    title: Optional[str] = Field(default=None, min_length=3, max_length=150)
    description: Optional[str] = Field(default=None, max_length=1000)
    date: Optional[datetime] = None
    location: Optional[str] = Field(default=None, min_length=3, max_length=200)
    capacity: Optional[int] = Field(default=None, gt=0)

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
