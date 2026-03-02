from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.async_session import get_db
from app.core.security import get_current_user
from app.db.models.user import User, Role
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.chatbot_service import chatbot_service
from app.core.security import RoleChecker

router = APIRouter()
rolechecker = RoleChecker([Role.ORGANIZER.value, Role.ATTENDEE.value])
    
@router.post("/", response_class=StreamingResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db), _: bool = Depends(rolechecker)):
    """
    Interact with the GenAI Chatbot via Server-Sent Events (SSE) streaming.
    """
    return StreamingResponse(
        chatbot_service.process_query(request.query, current_user, session), 
        media_type="text/event-stream"
    )
