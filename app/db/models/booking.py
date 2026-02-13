from datetime import datetime
from sqlmodel import Field, SQLModel
import uuid
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import Column, UniqueConstraint

class Booking(SQLModel, table=True):
    __tablename__ = "booking"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="unique_user_event_booking"),
    )

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            primary_key=True,
            unique=True,
            nullable=False,
            default=uuid.uuid4,
        )
    )
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    event_id: uuid.UUID = Field(foreign_key="event.id", nullable=False)
    booking_date: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow))
    status: str = Field(default="confirmed") # confirmed, cancelled
