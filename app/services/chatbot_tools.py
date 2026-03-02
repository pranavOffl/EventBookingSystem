import json
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.db.models.user import User
from langchain_core.tools import tool
from app.services.event_service import event_service
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services.booking_service import booking_service
from app.schemas.event import EventCreateRequest, EventUpdateRequest

def get_chatbot_tools(session: AsyncSession, user: User):
    
    @tool
    async def list_events() -> str:
        """
        List all events.
        """
        try:
            events = await event_service.get_all_events(session)
            return json.dumps([e.model_dump(mode="json") for e in events])
        except Exception as e:
            return f"Failed to list events: {str(e)}"

    @tool
    async def search_events(query: Optional[str] = None, location: Optional[str] = None, date: Optional[str] = None, upcoming_only: bool = True) -> str:
        """
        Search for events by title, description, location, or date.
        Args:
            query: Keywords to search in title/description (e.g., "Rock Concert", "Workshop").
            location: Filter by city or venue (e.g., "New York").
            date: Filter by specific date (YYYY-MM-DD).
            upcoming_only: Defaults to True. Set to False to include past events.
        """
        try:
            date_start = None
            date_end = None
            if date:
                # Simple parsing for single day filtering: Start of day to End of day
                try:
                    dt = datetime.fromisoformat(date)
                    date_start = dt.replace(hour=0, minute=0, second=0)
                    date_end = dt.replace(hour=23, minute=59, second=59)
                except ValueError:
                     return "Error: Invalid date format. Please use ISO format (YYYY-MM-DD)."

            events = await event_service.search_events(
                session, 
                query=query, 
                location=location, 
                date_start=date_start, 
                date_end=date_end,
                upcoming_only=upcoming_only,
                limit=10 
            )
            
            if not events:
                return "No events found matching this criteria. You MUST reply 'I do not have that information' and you are FORBIDDEN from guessing an event."
                
            return json.dumps([e.model_dump(mode="json") for e in events])
        except Exception as e:
            return f"Search failed: {str(e)}"

    @tool
    async def create_event(title: str, description: str, date: str, location: str, capacity: int) -> str:
        """
        Create a new event
        Args:
            title: Event title.
            description: Event description.
            date: ISO format date string (YYYY-MM-DDTHH:MM:SS)
            location: Venue location.
            capacity: Max number of attendees.
        """
        try:
            # Basic parsing, might need more robust handling
            event_date = datetime.fromisoformat(date)
            event_data = EventCreateRequest(
                title=title,
                description=description,
                date=event_date,
                location=location,
                capacity=capacity
            )
            new_event = await event_service.create_event(session, event_data, user)
            return f"Event created successfully! ID: {new_event.id}"
        except ValueError as e:
            return f"Invalid data format: {str(e)}"
        except Exception as e:
            return f"Creation failed: {str(e)}"

    @tool
    async def update_event(event_id: str, title: str = None, description: str = None, date: str = None, location: str = None, capacity: int = None) -> str:
        """
        Update an existing event. If you do not know the event_id, call search_events or list_events first to find it.
        Args:
            event_id: UUID of the event.
            title: New title (optional).
            description: New description (optional).
            date: New date (ISO format) (optional).
            location: New location (optional).
            capacity: New capacity (optional).
        """
        try:
            event = await event_service.get_event_by_id(session, UUID(event_id))
            if not event:
                return "Event not found."
            
            if event.organizer_id != user.id:
                    return "Error: You can only update events you created."

            update_kwargs = {
                "title": title,
                "description": description,
                "location": location,
                "capacity": capacity
            }
            # Remove None values so they don't overwrite existing data
            update_kwargs = {k: v for k, v in update_kwargs.items() if v is not None}
            
            if date:
                update_kwargs["date"] = datetime.fromisoformat(date)
                
            update_data = EventUpdateRequest(**update_kwargs)
                
            updated_event = await event_service.update_event(session, event, update_data)
            return f"Event updated successfully! ID: {updated_event.id}"
        except Exception as e:
            return f"Update failed: {str(e)}"

    @tool
    async def delete_event(event_id: str) -> str:
        """
        Delete an event. If you do not know the event_id, call search_events or list_events first to find it.
        Args:
            event_id: UUID of the event.
        """
        try:
            event = await event_service.get_event_by_id(session, UUID(event_id))
            if not event:
                return "Event not found."
            
            if event.organizer_id != user.id:
                    return "Error: You can only delete events you created."

            await event_service.delete_event(session, event)
            return "Event deleted successfully."
        except Exception as e:
            return f"Delete failed: {str(e)}"

    @tool
    async def create_booking(event_id: str) -> str:
        """
        Book a ticket for an event.
        Args:
            event_id: The UUID of the event to book.
        """
        try:
            booking = await booking_service.create_booking(session, user.id, UUID(event_id))
            return f"Booking successful! Booking ID: {booking.id}"
        except Exception as e:
            return f"Booking failed: {str(e)}"

    @tool
    async def get_user_bookings() -> str:
        """
        Show the current user's bookings.
        """
        bookings = await booking_service.get_user_bookings(session, user.id)
        return json.dumps([b.model_dump(mode="json") for b in bookings])

    @tool
    async def cancel_booking(booking_id: str) -> str:
        """
        Cancel a booking. If you do not know the booking_id, call get_user_bookings first to find it.
        Args:
            booking_id: UUID of the booking.
        """
        try:
            await booking_service.cancel_booking(session, UUID(booking_id), user)
            return "Booking cancelled successfully."
        except Exception as e:
            return f"Cancellation failed: {str(e)}"

    @tool
    async def get_event_attendees(event_id: str) -> str:
        """
        Get list of attendees for an event. If you do not know the event_id, call search_events or list_events first to find it.
        Args:
            event_id: UUID of the event.
        """
        try:
            event = await event_service.get_event_by_id(session, UUID(event_id))
            if not event:
                return "Event not found."
                
            if event.organizer_id != user.id:
                return "Error: You can only view attendees for your own events."

            attendees = await booking_service.get_event_attendees(session, UUID(event_id))
            return json.dumps([{"id": str(u.id), "email": u.email} for u in attendees])
        except Exception as e:
            return f"Failed to fetch attendees: {str(e)}"

    return {
        "list_events": list_events,
        "search_events": search_events,
        "create_event": create_event,
        "update_event": update_event,
        "delete_event": delete_event,
        "create_booking": create_booking,
        "get_user_bookings": get_user_bookings,
        "cancel_booking": cancel_booking,
        "get_event_attendees": get_event_attendees
    }
