from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models.user import User
from app.schemas.user import UserSignUpRequest, UserUpdate
from app.core.utils import generate_password_hash, verify_password

class UserService:
    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()
    
    async def user_exists(self, session: AsyncSession, email: str) -> bool:
        user = await self.get_user_by_email(session, email)
        return user is not None
    
    async def create_user(self, session: AsyncSession, user_data: UserSignUpRequest) -> User:
        password_hash = generate_password_hash(user_data.password)
        
        role = user_data.role.value if hasattr(user_data.role, "value") else user_data.role
        
        new_user = User(
            email=user_data.email,
            password=password_hash,
            role=role
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def authenticate_user(self, session: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(session, email)

        if not user:
            return None
        if not verify_password(password, user.password):
            return None
            
        return user
    
    async def update_user(self, session: AsyncSession, user: User, update_data: UserUpdate) -> User:
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.password is not None:
            password_hash = generate_password_hash(update_data.password)
            user.password = password_hash
        if update_data.role is not None:
             # Handle both Enum and string if passed manually
            user.role = update_data.role.value if hasattr(update_data.role, "value") else update_data.role
            
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

user_service = UserService()
