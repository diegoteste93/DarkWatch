from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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
