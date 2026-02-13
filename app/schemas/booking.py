from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlmodel import SQLModel

# Properties to return to client
class BookingRead(SQLModel):
    id: UUID
    event_id: UUID
    user_id: UUID
    booking_date: datetime
    status: str

class BookingCreate(SQLModel):
    event_id: UUID

class BookingMessageResponse(SQLModel):
    message: str
    booking: Optional[BookingRead] = None
