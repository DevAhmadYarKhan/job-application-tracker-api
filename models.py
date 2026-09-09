from sqlmodel import Field, SQLModel, String
from sqlalchemy import CheckConstraint
from typing import Literal
from datetime import datetime, UTC

# Repersents a table in database, attributes are column, objects are rows
class Application(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint(
            "NOT (status = 'saved' AND applied_at IS NOT NULL)",
            name="ck_saved_application_has_no_applied_at",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    company: str = Field(max_length=100)
    role: str = Field(max_length=100)
    status: Literal["saved", "applied", "interview", "offer", "rejected"] = Field(sa_type=String)
    job_url: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)
    applied_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))