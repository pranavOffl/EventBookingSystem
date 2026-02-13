from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from app.db.models.booking import Booking
import uuid
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import Column


class Event(SQLModel, table=True):
    __tablename__ = "event"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid.uuid4,
        )
    )
    title: str
    description: str
    date: datetime
    location: str
    capacity: int = Field(default=100)
    booked_seats: int = Field(default=0)
    organizer_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    organizer: Optional["User"] = Relationship(back_populates="events")
    attendees: List["User"] = Relationship(back_populates="booked_events", link_model=Booking)
