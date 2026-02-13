from sqlmodel import SQLModel
from pydantic import EmailStr, BaseModel, Field
from uuid import UUID
from enum import Enum

# Enums for Request
class UserSignUpRole(str, Enum):
    attendee = "attendee"
    organizer = "organizer"

# Request Schemas
class UserRequestBase(SQLModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)

class UserSignUpRequest(UserRequestBase):
    confirm_password: str = Field(min_length=8, max_length=64)
    role: UserSignUpRole = UserSignUpRole.attendee

class UserEmailUpdateRequest(BaseModel):
    email: EmailStr

class UserPasswordUpdateRequest(BaseModel):
    password: str = Field(min_length=8, max_length=64)
    confirm_password: str = Field(min_length=8, max_length=64)

class UserRoleUpdateRequest(BaseModel):
    role: UserSignUpRole

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=64)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=64)
    role: str | None = None

# Response Schemas
class UserResponseBase(SQLModel):
    id: UUID
    email: EmailStr
    role: str

class UserMessageResponse(SQLModel):
    message: str

class UserSignUpResponse(UserMessageResponse):
    user: UserResponseBase

class UserLoginResponse(UserMessageResponse):
    access_token: str
    refresh_token: str
    user: UserResponseBase

class UserRefreshTokenResponse(UserMessageResponse):
    access_token: str
