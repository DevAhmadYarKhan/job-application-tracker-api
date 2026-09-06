from pydantic import BaseModel, Field, model_validator
from typing import Literal
from datetime import datetime

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

class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None
    job_url: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)
    applied_at: datetime | None = None

    @model_validator(mode="after")
    def validate_appication_date(self):
        if self.status == "saved" and self.applied_at != None:
            raise ValueError("'applied_at' cannot be set to non-None while 'status' is 'saved'")
        return self