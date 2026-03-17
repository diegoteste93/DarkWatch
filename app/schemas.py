from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email:
            raise ValueError("Email inválido")
        local_part, domain_part = email.rsplit("@", 1)
        if not local_part or not domain_part:
            raise ValueError("Email inválido")
        return email


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)


class TargetCreate(BaseModel):
    type: str = Field(pattern="^(domain|email|keyword)$")
    value: str = Field(min_length=2, max_length=255)
    active: bool = True

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str) -> str:
        return value.strip().lower()


class TargetUpdate(BaseModel):
    value: str | None = Field(default=None, min_length=2, max_length=255)
    active: bool | None = None


class TenantSettingsUpdate(BaseModel):
    notification_email: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool | None = None


class PagingParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class FindingFilters(PagingParams):
    q: str | None = None
    source: str | None = None
    since: datetime | None = None
    sort: str = Field(default="last_seen_desc", pattern="^(last_seen_desc|last_seen_asc|first_seen_desc|first_seen_asc)$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    id: int
    email: str
    role: str
    tenant_id: int | None


class TenantResponse(BaseModel):
    id: int
    name: str
    notification_email: str | None
    created_at: datetime

    class Config:
        from_attributes = True


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


class RunResponse(BaseModel):
    id: int
    tenant_id: int
    trigger_type: str
    status: str
    processed_targets: int
    successful_targets: int
    failed_targets: int
    new_findings: int
    updated_findings: int
    started_at: datetime
    finished_at: datetime | None

    class Config:
        from_attributes = True


class TenantSettingsResponse(BaseModel):
    notification_email: str | None
    smtp_host: str | None
    smtp_port: int | None
    smtp_user: str | None
    smtp_from: str | None
    smtp_starttls: bool


class DashboardOverview(BaseModel):
    total_findings: int
    new_last_24h: int
    total_targets: int
    last_run_status: str | None
    failed_runs: int
