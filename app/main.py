from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models import Finding, Target, Tenant, User
from app.schemas import (
    FindingResponse,
    LoginRequest,
    TargetCreate,
    TargetResponse,
    TenantCreate,
    TenantResponse,
    TokenResponse,
)
from app.services.scanner import scan_tenant

app = FastAPI(title="DarkWatch")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
scheduler = AsyncIOScheduler()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub: str = payload.get("sub")
        if not sub:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.scalar(select(User).where(User.email == sub))
    if not user:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def authorize_tenant_access(tenant_id: int, user: User):
    if user.role == "admin":
        return
    if user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden tenant")


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
    return {"status": "ok"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@app.post("/tenants", response_model=TenantResponse)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    tenant = Tenant(name=payload.name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@app.post("/tenants/{tenant_id}/targets", response_model=TargetResponse)
def create_target(tenant_id: int, payload: TargetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    if not db.scalar(select(Tenant).where(Tenant.id == tenant_id)):
        raise HTTPException(status_code=404, detail="Tenant not found")
    target = Target(tenant_id=tenant_id, type=payload.type, value=payload.value, active=payload.active)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@app.get("/tenants/{tenant_id}/findings", response_model=list[FindingResponse])
def list_findings(
    tenant_id: int,
    since: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    authorize_tenant_access(tenant_id, user)
    stmt = select(Finding).where(Finding.tenant_id == tenant_id)
    if since:
        stmt = stmt.where(Finding.last_seen >= since)
    return db.scalars(stmt.order_by(Finding.last_seen.desc())).all()


@app.post("/tenants/{tenant_id}/scan")
async def trigger_scan(tenant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    authorize_tenant_access(tenant_id, user)
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    run = await scan_tenant(db, tenant, trigger_type="manual")
    return {"run_id": run.id, "status": run.status}
