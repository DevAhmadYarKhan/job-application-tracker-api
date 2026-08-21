from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

# We will not use this in @app.get("/applications") route just yet because the dummy data uses
# strings for applied_at etc
class ApplicationRead(BaseModel):
    id: int
    company: str = Field(max_length=100)
    role: str = Field(max_length=100)
    status: Literal["saved", "applied", "interview", "offer", "rejected"]
    job_url: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

class ApplicationCreate(BaseModel):
    company: str = Field(max_length=100)
    role: str = Field(max_length=100)
    status: Literal["saved", "applied", "interview", "offer", "rejected"]
    job_url: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)