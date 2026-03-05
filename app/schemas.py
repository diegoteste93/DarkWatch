from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email:
            raise ValueError("invalid email format")
        local_part, domain_part = email.rsplit("@", 1)
        if not local_part or not domain_part:
            raise ValueError("invalid email format")
        return email


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TenantCreate(BaseModel):
    name: str


class TenantResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TargetCreate(BaseModel):
    type: str = Field(pattern="^(domain|email|keyword)$")
    value: str
    active: bool = True


class TargetResponse(BaseModel):
    id: int
    tenant_id: int
    type: str
    value: str
    active: bool

    class Config:
        from_attributes = True


class FindingResponse(BaseModel):
    id: int
    target_id: int
    external_id: str
    source: str | None
    url: str | None
    username: str | None
    email: str | None
    leak_date: str | None
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True
