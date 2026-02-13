from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponseBase
from app.schemas.booking import BookingRead
from app.schemas.event import EventResponseBase
from typing import List

# Request schemas
class AdminRequestBase(BaseModel):
    email: EmailStr
    password: str

class AdminSignUpRequest(AdminRequestBase):
    confirm_password: str

class AdminEmailUpdateRequest(BaseModel):
    email: EmailStr

class AdminPasswordUpdateRequest(BaseModel):
    password: str
    confirm_password: str

class AdminUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    confirm_password: str | None = None

# Response schemas
class AdminResponseBase(BaseModel):
    id: UUID
    email: EmailStr
    role: str

class AdminMessageResponse(BaseModel):
    message: str

class AdminSignUpResponse(AdminMessageResponse):
    user: AdminResponseBase

class AdminLoginResponse(AdminMessageResponse):
    refresh_token: str
    access_token: str
    user: AdminResponseBase

class AdminRefreshTokenResponse(AdminMessageResponse):
    access_token: str

# User Management Schemas
class UserWithStats(UserResponseBase):
    booking_count: int = 0
    event_count: int = 0

class UserDetailResponse(UserWithStats):
    bookings: List[BookingRead] = []
    events: List[EventResponseBase] = []

class UserRoleUpdateAdmin(BaseModel):
    role: str
