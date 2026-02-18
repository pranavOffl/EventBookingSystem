# Event Booking System

An asynchronous Event Booking System built with FastAPI, designed to manage secure and scalable event reservations. It features a comprehensive Role-Based Access Control (RBAC) architecture, ensuring distinct and secure workflows for Admins, Organizers, and Attendees.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis
- [uv](https://github.com/astral-sh/uv) - Python package manager

## Quick Start

### 1. Install Dependencies

```bash
# Clone and enter directory
git clone <repository-url>
cd EventBookingSystem

# Install dependencies (creates .venv automatically)
uv sync
```

### 2. Configure Environment

Create a `.env` file:

```bash
# Database
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=booking
DB_HOST=localhost
DB_PORT= 5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security (JWT)
JWT_SECRET=e698218fbf1d9d46b06a6c1aa41b3124
JWT_ALGORITHM=HS256
JWT_EXPIRY=3600
ACCESS_TOKEN_EXPIRY=30
REFRESH_TOKEN_EXPIRY=10080
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb -U postgres eventbooking

# Run migrations
uv run alembic upgrade head
```

### 4. Run the Server

```bash
# Development mode
uv run uvicorn main:app --reload
```

## Docker Deployment

To build and run the project using Docker:

```bash
# 1. Build the Docker image from the current directory
docker build -t event-booking-system .

# 2. Run the container
# --network host: allows container to access local DB/Redis (Linux only)
# --env-file .env: loads environment variables from your local file
docker run --network host --env-file .env event-booking-system
```


API available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Development

### Rate Limiting

The API uses **SlowAPI** for rate limiting to prevent abuse.
- **Auth (Login/Signup)**: 5 requests / minute
- **Admin Actions**: 10-20 requests / minute
- **Event Management**: 5-10 requests / minute

If you hit a limit, you will receive a `429 Too Many Requests` response.

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply pending migrations
uv run alembic upgrade head
```

## Project Structure

```
EventBookingSystem/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/       
│   │   │   ├── admin/       # Admin routes (auth, users)
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── bookings.py  # Booking operations
│   │   │   ├── dashboard.py # Dashboard logic
│   │   │   └── events.py    # Event management
│   │   └── routers/         # Router aggregation
│   ├── core/                # Core modules
│   │   ├── config.py        # App config
│   │   ├── rate_limiter.py  # SlowAPI config
│   │   ├── redis.py         # Redis client
│   │   ├── security.py      # Auth & RBAC
│   │   └── utils.py         # Helpers
│   ├── db/
│   │   ├── models/          # SQLModel classes
│   │   └── async_session.py # Database session
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
│       ├── admin_service.py
│       ├── booking_service.py
│       ├── event_service.py
│       └── user_service.py
├── alembic/                 # Migration scripts
├── main.py                  # Entry point
├── pyproject.toml           # Dependencies
└── uv.lock                  # Locked dependencies
```

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /signup` - Register as Attendee or Organizer
- `POST /login` - Login to get Access/Refresh tokens
- `GET /refresh_token` - Get new access token
- `GET /logout` - Revoke token (Redis blocklist)

### Events (`/api/v1/events`)
- `GET /` - List events (Supports pagination `skip`/`limit` & `upcoming_only`)
- `GET /{id}` - Get event details
- `POST /` - Create event (Organizer/Admin only)
- `PATCH /{id}` - Update event (Owner/Admin only)
- `DELETE /{id}` - Delete event (Owner/Admin only)

### Bookings (`/api/v1/bookings`)
- `POST /` - Book a ticket (Concurrency Safe)
- `GET /my-bookings` - View user's bookings
- `DELETE /{id}` - Cancel booking (Reactivates seat)
- `GET /{event_id}` - View guest list (Organizer/Admin only)

### Admin (`/api/v1/admin`)
- `POST /auth/login` - Admin Login
- `GET /users/attendees` - List attendees with booking stats
- `GET /users/organizers` - List organizers with event stats
- `GET /users/details/{id}` - Full user profile
- `PATCH /users/role/{id}` - Promote/Demote users
- `DELETE /users/{id}` - Ban user account

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Async via SQLModel)
- **Cache**: Redis (Async)
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Package Manager**: uv
