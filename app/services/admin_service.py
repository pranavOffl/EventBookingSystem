from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.db.models.user import User, Role
from app.schemas.admin import AdminSignUpRequest, AdminUpdate
from app.core.utils import generate_password_hash, verify_password

class AdminService:
    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()
    
    async def get_user_by_id(self, session: AsyncSession, user_id: UUID) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        result = await session.exec(statement)
        return result.first()
    
    async def admin_exists(self, session: AsyncSession, email: str) -> bool:
        user = await self.get_user_by_email(session, email)
        return user is not None
    
    async def create_admin(self, session: AsyncSession, admin_data: AdminSignUpRequest) -> Optional[User]:
        password_hash = generate_password_hash(admin_data.password)
        new_admin = User(
            email=admin_data.email,
            password=password_hash,
            role=Role.ADMIN.value
        )

        session.add(new_admin)
        await session.commit()
        await session.refresh(new_admin)
        return new_admin

    async def authenticate_admin(self, session: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.get_user_by_email(session, email)

        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        if user.role != Role.ADMIN.value:
            return None
            
        return user
    
    async def update_admin(self, session: AsyncSession, user: User, update_data: AdminUpdate) -> User:
        if update_data.email is not None:
            user.email = update_data.email
        if update_data.password is not None:
            password_hash = generate_password_hash(update_data.password)
            user.password = password_hash
            
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    
    async def delete_admin(self, session: AsyncSession, user: User) -> bool:
        await session.delete(user)
        await session.commit()
        return True

    async def list_attendees(self, session: AsyncSession):
        """List all attendees with their booking counts."""
        # This requires importing Booking inside logic or top level.
        # Avoid circular imports if possible.
        from app.db.models.booking import Booking
        from sqlalchemy import func as sa_func

        # Select User and Count(Booking)
        # Left join to include users with 0 bookings
        statement = select(User, sa_func.count(Booking.id)).outerjoin(Booking, User.id == Booking.user_id).where(User.role == Role.ATTENDEE.value).group_by(User.id)
        
        result = await session.exec(statement)
        return result.all()

    async def list_organizers(self, session: AsyncSession):
        """List all organizers with their hosted event counts."""
        from app.db.models.event import Event
        from sqlalchemy import func as sa_func

        # Select User and Count(Event)
        statement = select(User, sa_func.count(Event.id)).outerjoin(Event, User.id == Event.organizer_id).where(User.role == Role.ORGANIZER.value).group_by(User.id)
        
        result = await session.exec(statement)
        return result.all()

    async def get_user_stats(self, session: AsyncSession, user_id: UUID):
        """Get user details with both booking and event counts."""
        from app.db.models.booking import Booking
        from app.db.models.event import Event
        from sqlalchemy import func as sa_func

        user = await self.get_user_by_id(session, user_id)
        if not user:
            return None, 0, 0

        # Count Bookings
        booking_count_stmt = select(sa_func.count(Booking.id)).where(Booking.user_id == user_id)
        booking_count = (await session.exec(booking_count_stmt)).first() or 0

        # Count Hosted Events
        event_count_stmt = select(sa_func.count(Event.id)).where(Event.organizer_id == user_id)
        event_count = (await session.exec(event_count_stmt)).first() or 0

        bookings_stmt = select(Booking).where(Booking.user_id == user_id)
        bookings = (await session.exec(bookings_stmt)).all()

        events_stmt = select(Event).where(Event.organizer_id == user_id)
        events = (await session.exec(events_stmt)).all()

        return user, booking_count, event_count, bookings, events

    async def update_user_role(self, session: AsyncSession, user: User, new_role: str) -> User:
        user.role = new_role
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

admin_service = AdminService()
