import asyncio

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.api_contracts import paginated_response
from app.core.security import get_password_hash
from app.models import Base, Target, Tenant, User
from app.schemas import LoginRequest
from app.services import scanner as scanner_module
from app.services.scanner import scan_tenant


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_tenant_duplicate_conflict(db_session: Session):
    db_session.add(Tenant(name="Acme"))
    db_session.commit()
    db_session.add(Tenant(name="Acme"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_target_duplicate_conflict(db_session: Session):
    tenant = Tenant(name="Beta")
    db_session.add(tenant)
    db_session.commit()

    db_session.add(Target(tenant_id=tenant.id, type="domain", value="acme.com", active=True))
    db_session.commit()
    db_session.add(Target(tenant_id=tenant.id, type="domain", value="acme.com", active=True))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_validation_login_email():
    with pytest.raises(Exception):
        LoginRequest(email="invalido", password="12345678")


def test_pagination_contract():
    payload = paginated_response([{"id": 1}], total=101, page=2, page_size=50)
    assert payload["pages"] == 3
    assert payload["page"] == 2


def test_scan_partial_failed(db_session: Session, monkeypatch):
    tenant = Tenant(name="Gamma", notification_email="soc@gamma.local")
    db_session.add(tenant)
    db_session.commit()

    user = User(email="admin@gamma.local", hashed_password=get_password_hash("Admin123!"), role="ADMIN", tenant_id=tenant.id)
    db_session.add(user)
    t1 = Target(tenant_id=tenant.id, type="email", value="a@gamma.local", active=True)
    t2 = Target(tenant_id=tenant.id, type="domain", value="gamma.com", active=True)
    db_session.add_all([t1, t2])
    db_session.commit()

    async def ok_email(self, *args, **kwargs):
        return {"items": [{"id": "x1", "source": "leak", "email": "a@gamma.local"}]}

    async def fail_domain(self, *args, **kwargs):
        raise RuntimeError("provider fail")

    monkeypatch.setattr(scanner_module.LeakRadarClient, "search_email", ok_email)
    monkeypatch.setattr(scanner_module.LeakRadarClient, "search_domain", fail_domain)
    monkeypatch.setattr(scanner_module.send_alert_email, "__call__", lambda *a, **k: True, raising=False)
    monkeypatch.setattr(scanner_module, "send_alert_email", lambda *a, **k: True)

    run = asyncio.run(scan_tenant(db_session, tenant, trigger_type="manual"))
    assert run.status == "partial_failed"
    assert run.successful_targets == 1
    assert run.failed_targets == 1
