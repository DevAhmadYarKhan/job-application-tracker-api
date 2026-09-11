# Job Application Tracker API

An asynchronous REST API for organising and tracking job applications throughout the hiring process. Built with FastAPI, SQLModel, and SQLite, it provides CRUD operations, status filtering, sorting, pagination, and application statistics.

> [!NOTE]
> This project is under active development. User ownership is represented in the data model, but authentication and user-scoped application routes are not yet complete. See [Current status](#current-status) before using the API beyond local development.

## Features

- Create, read, update, and delete job applications
- Track applications as `saved`, `applied`, `interview`, `offer`, or `rejected`
- Filter applications by status
- Sort by application, creation, or update date
- Paginate collection responses
- View totals grouped by application status
- Validate request and response data with Pydantic
- Use non-blocking database sessions with SQLModel and `aiosqlite`
- Explore automatically generated OpenAPI documentation

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [SQLModel](https://sqlmodel.tiangolo.com/) — database models and queries
- [SQLite](https://www.sqlite.org/) — local database
- [Pydantic](https://docs.pydantic.dev/) — data validation
- [pwdlib](https://frankie567.github.io/pwdlib/) — password hashing foundations

## Getting started

### Prerequisites

- Python 3.10 or newer
- Git

### Installation

Clone the repository and move into the project directory:

```bash
git clone https://github.com/DevAhmadYarKhan/job-application-tracker-api.git
cd job-application-tracker-api
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the runtime dependencies:

```bash
python -m pip install "fastapi[standard]" sqlmodel aiosqlite "pwdlib[argon2]"
```

Start the development server:

```bash
fastapi dev app/main.py
```

The API will be available at `http://127.0.0.1:8000`. The SQLite database file, `database.db`, is created automatically in the project root when the application starts.

## API documentation

With the server running, use either interactive documentation interface:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API reference

All application endpoints use the `/applications` prefix.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/applications/` | List applications with optional filtering, sorting, and pagination |
| `POST` | `/applications/` | Create an application |
| `GET` | `/applications/stats` | Return total and per-status application counts |
| `GET` | `/applications/{id}` | Return one application |
| `PATCH` | `/applications/{id}` | Partially update an application |
| `DELETE` | `/applications/{id}` | Delete an application |

### Application fields

| Field | Type | Required when creating | Notes |
| --- | --- | --- | --- |
| `company` | string | Yes | Maximum 100 characters |
| `role` | string | Yes | Maximum 100 characters |
| `status` | string | Yes | `saved`, `applied`, `interview`, `offer`, or `rejected` |
| `job_url` | string or null | No | Maximum 300 characters |
| `notes` | string or null | No | Maximum 500 characters |
| `applied_at` | datetime or null | Managed by the API | Must be null while the status is `saved` |
| `created_at` | datetime | Managed by the API | Set when the record is created |
| `updated_at` | datetime | Managed by the API | Refreshed when the record is updated |

Datetime values are returned as ISO 8601 timestamps. New non-saved applications receive the current UTC time as `applied_at`; saved applications receive `null`.

### List applications

```http
GET /applications/?status=interview&sort_by=updated_at&order=desc&page=1&page_size=20
```

Supported query parameters:

| Parameter | Allowed values | Default |
| --- | --- | --- |
| `status` | `saved`, `applied`, `interview`, `offer`, `rejected` | No filter |
| `sort_by` | `applied_at`, `created_at`, `updated_at` | Database order |
| `order` | `asc`, `desc` | `asc` |
| `page` | Integer greater than or equal to 1 | `1` |
| `page_size` | Integer from 1 to 100 | `20` |

Example:

```bash
curl "http://127.0.0.1:8000/applications/?status=interview&sort_by=updated_at&order=desc"
```

### Create an application

```bash
curl -X POST "http://127.0.0.1:8000/applications/" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Acme Technologies",
    "role": "Backend Developer",
    "status": "applied",
    "job_url": "https://example.com/jobs/123",
    "notes": "Applied through the company website."
  }'
```

Example response:

```json
{
  "id": 1,
  "company": "Acme Technologies",
  "role": "Backend Developer",
  "status": "applied",
  "job_url": "https://example.com/jobs/123",
  "notes": "Applied through the company website.",
  "applied_at": "2026-09-11T18:30:00Z",
  "created_at": "2026-09-11T18:30:00Z",
  "updated_at": "2026-09-11T18:30:00Z"
}
```

### Update an application

Only include fields that should change:

```bash
curl -X PATCH "http://127.0.0.1:8000/applications/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "interview",
    "notes": "Technical interview scheduled."
  }'
```

When moving an application back to `saved`, include `"applied_at": null` in the same request.

### View statistics

```bash
curl "http://127.0.0.1:8000/applications/stats"
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

Successful deletions return `204 No Content`. Requests with invalid path, query, or body values return FastAPI validation errors; requests for missing application IDs return `404 Not Found`.

## Project structure

```text
app/
├── main.py                  # FastAPI application and startup lifecycle
├── database.py              # Async SQLite engine and session dependency
├── models.py                # SQLModel database tables
├── schemas.py               # Request and response models
├── routes/
│   └── applications.py      # HTTP routes
└── services/
    └── applications.py      # Database operations and business logic
```

The database schema is created automatically at startup with `SQLModel.metadata.create_all()`. Database files are excluded from version control, so each local checkout starts with its own data.

## Current status

The `User` model, password hashing helpers, and the relationship between users and applications are present. The authentication flow and user routes are not yet implemented, and application creation does not yet attach an authenticated user ID. A fresh database therefore requires that ownership integration to be completed before the `POST /applications/` workflow is fully functional.

Other production-oriented additions still to consider include database migrations, automated tests, dependency pinning, environment-based configuration, and deployment configuration.

## License

This project is available under the [MIT License](LICENSE).
