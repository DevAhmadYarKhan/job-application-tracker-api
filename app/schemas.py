from pydantic import BaseModel, Field, model_validator, EmailStr
from typing import Literal
from datetime import datetime

# Schema used to validate the 'shape' of data representing an application being returned by an endpoint
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



# Schema used to validate data representing new application instance to be created
class ApplicationCreate(BaseModel):
    company: str = Field(max_length=100)
    role: str = Field(max_length=100)
    status: Literal["saved", "applied", "interview", "offer", "rejected"]
    job_url: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)



# Schema used to validate data for patching an application, hence most fields are optional
class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    status: Literal["saved", "applied", "interview", "offer", "rejected"] | None = None
    job_url: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=500)
    applied_at: datetime | None = None

    # Validator checks before creating ApplicationUpdate instance that certain fields are not being
    # made null, and raises error if they are.
    @model_validator(mode="before")
    @classmethod
    def reject_nulls(cls, data):
        non_nullable_fields = {
            "company",
            "role",
            "status",
            "job_url",
            "notes",
        }

        if isinstance(data, dict):
            null_fields = []

            for key, value in data.items():
                if key in non_nullable_fields and value is None:
                    null_fields.append(key)

            if null_fields:
                raise ValueError(f"Fields cannot be null: {', '.join(null_fields)}")

        return data

    # Model validator with mode="after" runs after the whole model has been validated. This ensures
    # that you cannot update an application such that the status has value 'saved' but there is
    # also an applied_at value
    @model_validator(mode="after")
    def validate_appication_date(self):
        if self.status == "saved" and self.applied_at is not None:
            raise ValueError("'applied_at' cannot be set to non-None while 'status' is 'saved'")
        return self

    

class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=100)
    username: str = Field(max_length=100)
    password: str = Field(min_length=1, max_length=100)


class UserRead(BaseModel):
    id: int
    email: EmailStr = Field(max_length=255)
    username: str = Field(max_length=100)


class UserLogin(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(min_length=1, max_length=100)


class Token(BaseModel):
    access_token: str
    token_type: str