# Job Application Tracker API

An asynchronous REST API for managing job applications throughout the hiring process. It provides JWT authentication, user-scoped CRUD operations, filtering, sorting, pagination, and application statistics.

## Features

- Create an account and sign in with an OAuth2 password flow
- Authenticate requests with short-lived JWT bearer tokens
- Keep each user's applications private
- Create, read, update, and delete job applications
- Track applications as `saved`, `applied`, `interview`, `offer`, or `rejected`
- Filter by status and sort by application, creation, or update date
- Paginate application lists
- View totals grouped by application status
- Validate request and response data with Pydantic
- Use asynchronous SQLModel sessions with SQLite and `aiosqlite`
- Explore the API through automatically generated OpenAPI documentation

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) — API framework and OpenAPI documentation
- [SQLModel](https://sqlmodel.tiangolo.com/) — database models and queries
- [SQLite](https://www.sqlite.org/) with [aiosqlite](https://aiosqlite.omnilib.dev/) — asynchronous local persistence
- [Pydantic](https://docs.pydantic.dev/) — request and response validation
- [PyJWT](https://pyjwt.readthedocs.io/) — JWT creation and validation
- [pwdlib](https://frankie567.github.io/pwdlib/) — password hashing

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

Install the runtime dependencies:

```bash
python -m pip install "fastapi[standard]" sqlmodel aiosqlite "pwdlib[argon2]" PyJWT python-dotenv
```

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./database.db
SECRET_KEY=replace-this-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a suitable secret with Python, then use the output as `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the development server:

```bash
fastapi dev app/main.py
```

The API is now available at `http://127.0.0.1:8000`. On first startup, SQLModel creates the tables and the configured SQLite database automatically.

## API documentation

With the server running, open either interactive documentation interface:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Swagger UI can also perform the login flow for protected endpoints: create an account with `POST /signup`, select **Authorize**, and enter the account's username and password.

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

Tokens use the HS256 algorithm and expire after `ACCESS_TOKEN_EXPIRE_MINUTES`. Passwords are stored as hashes rather than plaintext.

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
| `applied_at` | datetime or null | No (not accepted) | Set automatically on creation; it can be changed later with `PATCH` |
| `id` | integer | Managed by the API | Returned in application responses |
| `created_at` | datetime | Managed by the API | Set when the application is created |
| `updated_at` | datetime | Managed by the API | Refreshed when the application is updated |

Datetime values use ISO 8601 format. Ownership is derived from the bearer token; clients do not send or receive a `user_id` in application payloads.

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

When changing a previously applied application back to `saved`, include `"applied_at": null` in the same request. This maintains the rule that saved applications cannot have an application date.

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

## Project structure

```text
.
├── app/
│   ├── main.py                  # FastAPI application and startup lifecycle
│   ├── database.py              # Async engine and session dependency
│   ├── models.py                # User and application database tables
│   ├── schemas.py               # Request and response models
│   ├── routes/
│   │   ├── applications.py      # Protected application endpoints
│   │   └── auth.py              # Sign-up, login, and current-user endpoints
│   └── services/
│       ├── applications.py      # Application queries and business logic
│       └── auth.py              # Password and JWT authentication logic
├── config.py                    # Environment-based configuration
└── README.md
```

The application creates its schema with `SQLModel.metadata.create_all()` at startup. It does not currently include database migrations, automated tests, or a pinned dependency file, so it is best suited to local development while those production-oriented pieces are added.

## License

This project is available under the [MIT License](LICENSE).
