from datetime import datetime, timedelta
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import SQLAlchemyError, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api_contracts import error_response, paginated_response, success_response
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.exceptions import APIError, ProviderUnavailableError, ScanAlreadyRunningError
from app.models import Finding, Run, Target, Tenant, User
from app.schemas import (
    DashboardOverview,
    FindingResponse,
    LoginRequest,
    RunResponse,
    TargetCreate,
    TargetResponse,
    TargetUpdate,
    TenantCreate,
    TenantResponse,
    TenantSettingsResponse,
    TenantSettingsUpdate,
    TenantUpdate,
)
from app.services.mailer import send_alert_email
from app.services.scanner import scan_tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DarkWatch")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
scheduler = AsyncIOScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def api_error_handler(_: Request, exc: APIError):
    logger.warning("api error code=%s detail=%s", exc.code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content=error_response(str(exc.detail), exc.code, exc.status_code))


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError):
    logger.exception("integrity error")
    return JSONResponse(status_code=409, content=error_response("Resource conflict", "CONFLICT", 409))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    logger.warning("validation error: %s", exc.errors())
    return JSONResponse(status_code=422, content=error_response("Validation error", "VALIDATION_ERROR", 422))


@app.exception_handler(ProviderUnavailableError)
async def provider_error_handler(_: Request, exc: ProviderUnavailableError):
    logger.exception("provider unavailable")
    return JSONResponse(status_code=503, content=error_response(str(exc), "PROVIDER_UNAVAILABLE", 503))


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError):
    logger.exception("database error")
    return JSONResponse(status_code=500, content=error_response("Internal error", "INTERNAL_ERROR", 500))


@app.exception_handler(Exception)
async def generic_error_handler(_: Request, exc: Exception):
    logger.exception("unexpected error")
    return JSONResponse(status_code=500, content=error_response("Internal error", "INTERNAL_ERROR", 500))


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError as exc:
        raise APIError(401, "Token expired", "INVALID_TOKEN") from exc
    except JWTError as exc:
        raise APIError(401, "Invalid token", "INVALID_TOKEN") from exc

    sub: str | None = payload.get("sub")
    if not sub:
        raise APIError(401, "Invalid token", "INVALID_TOKEN")

    user = db.scalar(select(User).where(User.email == sub))
    if not user:
        raise APIError(401, "Invalid token", "INVALID_TOKEN")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role.upper() != "ADMIN":
        raise APIError(403, "Access denied", "ACCESS_DENIED")
    return user


def authorize_tenant_access(tenant_id: int, user: User):
    if user.role.upper() == "ADMIN":
        return
    if user.tenant_id != tenant_id:
        raise APIError(403, "Access denied", "ACCESS_DENIED")


@app.on_event("startup")
async def startup_event():
    scheduler.add_job(scheduled_scan, "interval", hours=6, id="tenant_scan", replace_existing=True)
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown(wait=False)


async def scheduled_scan():
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        tenants = db.scalars(select(Tenant)).all()
        for tenant in tenants:
            await scan_tenant(db, tenant, trigger_type="scheduled")
    finally:
        db.close()


@app.get("/health")
def health():
    return success_response({"status": "ok"})


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.info("login failed email=%s", payload.email)
        raise APIError(401, "Invalid credentials", "UNAUTHORIZED")
    token = create_access_token(user.email)
    logger.info("login success user_id=%s email=%s", user.id, user.email)
    return success_response({"access_token": token, "token_type": "bearer"})


@app.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return success_response({"id": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id})


@app.get("/tenants")
def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    q: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    stmt = select(Tenant)
    count_stmt = select(func.count(Tenant.id))
    if q:
        stmt = stmt.where(Tenant.name.ilike(f"%{q.strip()}%"))
        count_stmt = count_stmt.where(Tenant.name.ilike(f"%{q.strip()}%"))
    total = db.scalar(count_stmt) or 0
    items = db.scalars(stmt.order_by(Tenant.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return paginated_response([TenantResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@app.post("/tenants", status_code=201)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    exists = db.scalar(select(Tenant).where(func.lower(Tenant.name) == payload.name.lower()))
    if exists:
        raise APIError(409, "Tenant already exists", "TENANT_DUPLICATE")
    tenant = Tenant(name=payload.name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    logger.info("tenant created tenant_id=%s", tenant.id)
    return success_response(TenantResponse.model_validate(tenant).model_dump())


@app.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    return success_response(TenantResponse.model_validate(tenant).model_dump())


@app.patch("/tenants/{tenant_id}")
def patch_tenant(tenant_id: int, payload: TenantUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    if payload.name:
        tenant.name = payload.name.strip()
    db.commit()
    db.refresh(tenant)
    return success_response(TenantResponse.model_validate(tenant).model_dump())


@app.get("/tenants/{tenant_id}/targets")
def list_targets(
    tenant_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    authorize_tenant_access(tenant_id, user)
    stmt = select(Target).where(Target.tenant_id == tenant_id)
    count_stmt = select(func.count(Target.id)).where(Target.tenant_id == tenant_id)
    if q:
        stmt = stmt.where(Target.value.ilike(f"%{q.strip().lower()}%"))
        count_stmt = count_stmt.where(Target.value.ilike(f"%{q.strip().lower()}%"))
    total = db.scalar(count_stmt) or 0
    items = db.scalars(stmt.order_by(Target.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return paginated_response([TargetResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@app.post("/tenants/{tenant_id}/targets", status_code=201)
def create_target(tenant_id: int, payload: TargetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    duplicate = db.scalar(
        select(Target).where(
            Target.tenant_id == tenant_id,
            Target.type == payload.type,
            func.lower(Target.value) == payload.value.lower(),
        )
    )
    if duplicate:
        raise APIError(409, "Target already exists", "TARGET_DUPLICATE")
    target = Target(tenant_id=tenant_id, type=payload.type, value=payload.value, active=payload.active)
    db.add(target)
    db.commit()
    db.refresh(target)
    logger.info("target created tenant_id=%s target_id=%s", tenant_id, target.id)
    return success_response(TargetResponse.model_validate(target).model_dump())


@app.patch("/tenants/{tenant_id}/targets/{target_id}")
def patch_target(
    tenant_id: int,
    target_id: int,
    payload: TargetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    authorize_tenant_access(tenant_id, user)
    target = db.scalar(select(Target).where(Target.id == target_id, Target.tenant_id == tenant_id))
    if not target:
        raise APIError(404, "Target not found", "RESOURCE_NOT_FOUND")
    if payload.value is not None:
        target.value = payload.value.strip().lower()
    if payload.active is not None:
        target.active = payload.active
    db.commit()
    db.refresh(target)
    return success_response(TargetResponse.model_validate(target).model_dump())


@app.get("/tenants/{tenant_id}/findings")
def list_findings(
    tenant_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    q: str | None = None,
    source: str | None = None,
    since: datetime | None = None,
    sort: str = Query("last_seen_desc", pattern="^(last_seen_desc|last_seen_asc|first_seen_desc|first_seen_asc)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    authorize_tenant_access(tenant_id, user)
    stmt = select(Finding).where(Finding.tenant_id == tenant_id)
    count_stmt = select(func.count(Finding.id)).where(Finding.tenant_id == tenant_id)
    if q:
        expr = f"%{q.strip().lower()}%"
        condition = or_(func.lower(Finding.email).ilike(expr), func.lower(Finding.username).ilike(expr), func.lower(Finding.url).ilike(expr))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    if source:
        stmt = stmt.where(Finding.source == source)
        count_stmt = count_stmt.where(Finding.source == source)
    if since:
        stmt = stmt.where(Finding.last_seen >= since)
        count_stmt = count_stmt.where(Finding.last_seen >= since)
    ordering = {
        "last_seen_desc": Finding.last_seen.desc(),
        "last_seen_asc": Finding.last_seen.asc(),
        "first_seen_desc": Finding.first_seen.desc(),
        "first_seen_asc": Finding.first_seen.asc(),
    }
    total = db.scalar(count_stmt) or 0
    items = db.scalars(stmt.order_by(ordering[sort]).offset((page - 1) * page_size).limit(page_size)).all()
    return paginated_response([FindingResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@app.get("/tenants/{tenant_id}/runs")
def list_runs(
    tenant_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    authorize_tenant_access(tenant_id, user)
    total = db.scalar(select(func.count(Run.id)).where(Run.tenant_id == tenant_id)) or 0
    items = db.scalars(select(Run).where(Run.tenant_id == tenant_id).order_by(Run.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return paginated_response([RunResponse.model_validate(i).model_dump() for i in items], total, page, page_size)


@app.get("/tenants/{tenant_id}/runs/{run_id}")
def get_run(tenant_id: int, run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    run = db.scalar(select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id))
    if not run:
        raise APIError(404, "Run not found", "RESOURCE_NOT_FOUND")
    return success_response(RunResponse.model_validate(run).model_dump())


@app.post("/tenants/{tenant_id}/scan")
async def trigger_scan(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    running = db.scalar(select(Run).where(Run.tenant_id == tenant_id, Run.status.in_(["pending", "running"])))
    if running:
        raise ScanAlreadyRunningError()
    logger.info("scan started tenant_id=%s user_email=%s", tenant_id, user.email)
    run = await scan_tenant(db, tenant, trigger_type="manual")
    logger.info("scan finished tenant_id=%s run_id=%s status=%s", tenant_id, run.id, run.status)
    return success_response({"run_id": run.id, "status": run.status})


@app.get("/tenants/{tenant_id}/settings")
def get_settings(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    return success_response(
        TenantSettingsResponse(
            notification_email=tenant.notification_email,
            smtp_host=tenant.smtp_host,
            smtp_port=tenant.smtp_port,
            smtp_user=tenant.smtp_user,
            smtp_from=tenant.smtp_from,
            smtp_starttls=tenant.smtp_starttls,
        ).model_dump()
    )


@app.patch("/tenants/{tenant_id}/settings")
def patch_settings(
    tenant_id: int,
    payload: TenantSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    for field in ["notification_email", "smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from", "smtp_starttls"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(tenant, field, value)
    db.commit()
    return success_response({"updated": True})


@app.post("/tenants/{tenant_id}/settings/test-email")
def test_email(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise APIError(404, "Tenant not found", "RESOURCE_NOT_FOUND")
    recipient = tenant.notification_email or user.email
    sent = send_alert_email(recipient, "[DarkWatch] Test SMTP", "Teste de envio SMTP", tenant=tenant)
    if not sent:
        raise APIError(503, "SMTP failure", "SMTP_FAILURE")
    return success_response({"sent": True})


@app.get("/admin/dashboard/overview")
def admin_dashboard(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total_findings = db.scalar(select(func.count(Finding.id))) or 0
    total_targets = db.scalar(select(func.count(Target.id))) or 0
    new_last_24h = db.scalar(select(func.count(Finding.id)).where(Finding.first_seen >= datetime.utcnow() - timedelta(hours=24))) or 0
    failed_runs = db.scalar(select(func.count(Run.id)).where(Run.status.in_(["failed", "partial_failed"]))) or 0
    last_run = db.scalar(select(Run).order_by(Run.id.desc()))
    payload = DashboardOverview(
        total_findings=total_findings,
        new_last_24h=new_last_24h,
        total_targets=total_targets,
        last_run_status=last_run.status if last_run else None,
        failed_runs=failed_runs,
    ).model_dump()
    return success_response(payload)


@app.get("/tenants/{tenant_id}/dashboard/overview")
def tenant_dashboard(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    total_findings = db.scalar(select(func.count(Finding.id)).where(Finding.tenant_id == tenant_id)) or 0
    total_targets = db.scalar(select(func.count(Target.id)).where(Target.tenant_id == tenant_id)) or 0
    new_last_24h = db.scalar(
        select(func.count(Finding.id)).where(Finding.tenant_id == tenant_id, Finding.first_seen >= datetime.utcnow() - timedelta(hours=24))
    ) or 0
    failed_runs = db.scalar(
        select(func.count(Run.id)).where(Run.tenant_id == tenant_id, Run.status.in_(["failed", "partial_failed"]))
    ) or 0
    last_run = db.scalar(select(Run).where(Run.tenant_id == tenant_id).order_by(Run.id.desc()))
    payload = DashboardOverview(
        total_findings=total_findings,
        new_last_24h=new_last_24h,
        total_targets=total_targets,
        last_run_status=last_run.status if last_run else None,
        failed_runs=failed_runs,
    ).model_dump()
    return success_response(payload)
