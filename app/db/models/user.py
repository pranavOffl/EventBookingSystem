from typing import List
from sqlmodel import Field, SQLModel, Relationship
from app.db.models.booking import Booking
import uuid
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import Enum as SAEnum, Column
from enum import Enum

class Role(str, Enum):
    ORGANIZER = "organizer"
    ATTENDEE = "attendee"
    ADMIN = "admin"

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid.uuid4,
        )
    )
    email: str = Field(unique=True, index=True)
    password: str
    role: Role = Field(
        sa_column=Column(SAEnum(Role, name="role_enum", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=Role.ATTENDEE),
        default=Role.ATTENDEE
    )
    
    events: List["Event"] = Relationship(back_populates="organizer")
    
    # Relationship to events booked by this user
    booked_events: List["Event"] = Relationship(back_populates="attendees", link_model=Booking)
