# Job Application Tracker API

An asynchronous REST API for managing job applications throughout the hiring process. It provides JWT authentication, user-scoped CRUD operations, filtering, sorting, pagination, and status statistics.

## Features

- Create an account and sign in with the OAuth2 password flow
- Authenticate requests with expiring JWT bearer tokens
- Keep every user's job applications private
- Create, read, update, and delete applications
- Track applications as `saved`, `applied`, `interview`, `offer`, or `rejected`
- Filter by status, sort by date, and paginate results
- View totals grouped by application status
- Manage schema changes with Alembic migrations
- Validate request and response data with Pydantic
- Run API integration tests against an isolated in-memory SQLite database
- Explore the API through generated OpenAPI documentation

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) — API framework and OpenAPI documentation
- [SQLModel](https://sqlmodel.tiangolo.com/) and SQLAlchemy — data models and database queries
- [SQLite](https://www.sqlite.org/) with [aiosqlite](https://aiosqlite.omnilib.dev/) or PostgreSQL with [asyncpg](https://magicstack.github.io/asyncpg/) — asynchronous persistence
- [Alembic](https://alembic.sqlalchemy.org/) — database migrations
- [Pydantic](https://docs.pydantic.dev/) — request and response validation
- [PyJWT](https://pyjwt.readthedocs.io/) — JWT creation and validation
- [pwdlib](https://frankie567.github.io/pwdlib/) — Argon2 password hashing
- [pytest](https://docs.pytest.org/) and [HTTPX](https://www.python-httpx.org/) — async integration testing

## Getting started

### Prerequisites

- Python 3.11 or newer
- Git

### Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/DevAhmadYarKhan/job-application-tracker-api.git
cd job-application-tracker-api
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project and its development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For a runtime-only installation, use `python -m pip install -e .` instead.

### Configuration

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./database.db
SECRET_KEY=replace-this-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy async database URL for SQLite or PostgreSQL | `sqlite+aiosqlite:///./database.db` |
| `SECRET_KEY` | Secret used to sign JWTs | A long random string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Bearer-token lifetime in minutes | `30` |

Generate a suitable secret and copy its output into `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

To use PostgreSQL instead, create a database and set `DATABASE_URL` in `.env` to an asyncpg URL, for example:

```dotenv
DATABASE_URL=postgresql+asyncpg://tracker:password@localhost:5432/job_tracker
```

The application and Alembic both read `DATABASE_URL` from the environment or `.env` file.

### Create the database

Apply all database migrations before starting the API:

```bash
alembic upgrade head
```

The SQLite URL shown above creates `database.db` in the project root. For PostgreSQL, create the database before running the migration. When the models change, create and review a migration with `alembic revision --autogenerate -m "describe the change"`, then apply it with `alembic upgrade head`.

### Run the API

Start the development server:

```bash
fastapi dev app/main.py
```

The API is available at `http://127.0.0.1:8000`.

## API documentation

With the server running, open either interactive documentation interface:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Swagger UI can also perform the login flow for protected endpoints. Create an account with `POST /signup`, select **Authorize**, and enter the account's username and password.

## Authentication

Sign up by sending JSON to `POST /signup`:

```bash
curl -X POST "http://127.0.0.1:8000/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "username": "developer",
    "password": "choose-a-strong-password"
  }'
```

Log in by sending form data to `POST /token`. The `username` field expects the username chosen at sign-up, not the email address.

```bash
curl -X POST "http://127.0.0.1:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=developer&password=choose-a-strong-password"
```

The response contains a bearer token:

```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

Copy the token into an environment variable for the examples below:

```bash
TOKEN="<jwt-token>"
```

Pass it with every protected request:

```bash
curl "http://127.0.0.1:8000/me" \
  -H "Authorization: Bearer $TOKEN"
```

Tokens use the HS256 algorithm and expire after `ACCESS_TOKEN_EXPIRE_MINUTES`. Passwords are stored as Argon2 hashes rather than plaintext.

## API reference

| Method | Endpoint | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/signup` | Public | Create a user account |
| `POST` | `/token` | Public | Exchange username and password form data for a JWT |
| `GET` | `/me` | Bearer token | Return the current user's public profile |
| `GET` | `/applications/` | Bearer token | List the current user's applications |
| `POST` | `/applications/` | Bearer token | Create an application for the current user |
| `GET` | `/applications/stats` | Bearer token | Return the current user's application counts |
| `GET` | `/applications/{id}` | Bearer token | Return one application owned by the current user |
| `PATCH` | `/applications/{id}` | Bearer token | Partially update an owned application |
| `DELETE` | `/applications/{id}` | Bearer token | Delete an owned application |

### Application fields

| Field | Type | Required when creating | Notes |
| --- | --- | --- | --- |
| `company` | string | Yes | Maximum 100 characters |
| `role` | string | Yes | Maximum 100 characters |
| `status` | string | Yes | `saved`, `applied`, `interview`, `offer`, or `rejected` |
| `job_url` | string or null | No | Maximum 300 characters |
| `notes` | string or null | No | Maximum 500 characters |
| `applied_at` | datetime or null | No | Set by the API on creation; may be changed with `PATCH` |
| `id` | integer | Managed by the API | Returned in application responses |
| `created_at` | datetime | Managed by the API | Set when the application is created |
| `updated_at` | datetime | Managed by the API | Refreshed when the application is updated |

Datetime values use ISO 8601 format, and API-generated timestamps are based on UTC. Ownership is derived from the bearer token; clients do not send or receive a `user_id` in application payloads. Clients cannot set `applied_at` when creating an application. A newly created `saved` application has no `applied_at`; other statuses receive the current time.

### Create an application

```bash
curl -X POST "http://127.0.0.1:8000/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Acme Technologies",
    "role": "Backend Developer",
    "status": "applied",
    "job_url": "https://example.com/jobs/123",
    "notes": "Applied through the company website."
  }'
```

### List applications

```bash
curl "http://127.0.0.1:8000/applications/?status=interview&sort_by=updated_at&order=desc&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

Supported query parameters:

| Parameter | Allowed values | Default |
| --- | --- | --- |
| `status` | `saved`, `applied`, `interview`, `offer`, `rejected` | No filter |
| `sort_by` | `applied_at`, `created_at`, `updated_at` | Database order |
| `order` | `asc`, `desc` | `asc` |
| `page` | Integer greater than or equal to 1 | `1` |
| `page_size` | Integer from 1 to 100 | `20` |

### Update an application

Only include fields that should change:

```bash
curl -X PATCH "http://127.0.0.1:8000/applications/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "interview",
    "notes": "Technical interview scheduled."
  }'
```

Changing an application to `saved` automatically clears `applied_at`. A request that sets both `status` to `saved` and `applied_at` to a non-null value is rejected.

### View statistics

```bash
curl "http://127.0.0.1:8000/applications/stats" \
  -H "Authorization: Bearer $TOKEN"
```

Example response:

```json
{
  "total": 12,
  "saved": 2,
  "applied": 5,
  "interview": 3,
  "offer": 1,
  "rejected": 1
}
```

Successful deletions return `204 No Content`. Missing, expired, or invalid bearer credentials return `401 Unauthorized`. FastAPI returns validation errors for invalid path, query, form, or JSON values.

## Testing

Install the development dependencies, ensure the three environment variables above are defined, and run:

```bash
pytest
```

The current integration suite covers the application endpoints. It replaces the application's database session and authenticated-user dependencies, then creates a fresh in-memory SQLite schema for each test. It does not modify the database configured by `DATABASE_URL`.

## Project structure

```text
.
├── app/
│   ├── main.py                  # FastAPI application and router registration
│   ├── config.py                # Environment-based configuration
│   ├── database.py              # Async engine and session dependency
│   ├── models.py                # User and application database tables
│   ├── schemas.py               # Request and response models
│   ├── routes/
│   │   ├── applications.py      # Protected application endpoints
│   │   └── auth.py              # Sign-up, login, and current-user endpoints
│   └── services/
│       ├── applications.py      # Application queries and business logic
│       └── auth.py              # Password and JWT authentication logic
├── migrations/                  # Alembic migration environment and revisions
├── tests/integration/           # Async API integration tests
├── alembic.ini                  # Alembic configuration
├── pyproject.toml               # Package metadata, dependencies, and pytest settings
└── README.md
```

## License

This project is available under the [MIT License](LICENSE).
