from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponseBase
from app.schemas.booking import BookingRead
from app.schemas.event import EventResponseBase
from typing import List

# Request schemas
class AdminRequestBase(BaseModel):
    email: EmailStr = Field(examples=["admin@example.com"])
    password: str = Field(min_length=8, max_length=64, examples=["password123"])

class AdminSignUpRequest(AdminRequestBase):
    confirm_password: str = Field(min_length=8, max_length=64, examples=["password123"])

class AdminEmailUpdateRequest(BaseModel):
    email: EmailStr

class AdminPasswordUpdateRequest(BaseModel):
    password: str = Field(min_length=8, max_length=64)
    confirm_password: str = Field(min_length=8, max_length=64)

class AdminUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=64)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=64)

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
