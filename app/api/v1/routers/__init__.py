from fastapi import APIRouter

from app.api.v1.endpoints.admin import auth as admin_auth
from app.api.v1.endpoints.admin import dashboard as admin_dashboard
from app.api.v1.endpoints.admin import users as admin_users
from app.api.v1.endpoints import auth as user_auth
from app.api.v1.endpoints import dashboard as user_dashboard
from app.api.v1.endpoints import events, bookings

api_router = APIRouter()

api_router.include_router(admin_auth.router, prefix="/admin", tags=["Admin Auth"])
api_router.include_router(admin_dashboard.router, prefix="/admin", tags=["Admin Dashboard"])
api_router.include_router(admin_users.router, prefix="/admin/users", tags=["Admin User Management"])
api_router.include_router(user_auth.router, prefix="/user", tags=["User Auth"])
api_router.include_router(user_dashboard.router, prefix="/user", tags=["User Dashboard"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])

