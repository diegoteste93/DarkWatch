import hashlib
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.leakradar_client import LeakRadarClient
from app.models import Alert, Finding, Run, Target, Tenant, User
from app.services.mailer import send_alert_email


def _extract_items(payload: dict) -> list[dict]:
    for key in ("results", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [i for i in value if isinstance(i, dict)]
    return []


def _external_id(item: dict, target: Target) -> str:
    if item.get("id"):
        return str(item["id"])
    basis = "|".join(
        [
            target.type,
            target.value,
            str(item.get("url", "")),
            str(item.get("username") or item.get("email") or ""),
            str(item.get("source", "")),
            str(item.get("leak_date", "")),
        ]
    )
    return hashlib.sha256(basis.encode()).hexdigest()


async def scan_tenant(db: Session, tenant: Tenant, trigger_type: str = "scheduled") -> Run:
    run = Run(tenant_id=tenant.id, trigger_type=trigger_type, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    client = LeakRadarClient(settings.leakradar_api_key, settings.leakradar_base_url)
    targets = db.scalars(select(Target).where(Target.tenant_id == tenant.id, Target.active.is_(True))).all()

    try:
        for target in targets:
            if target.type == "email":
                payload = await client.search_email(target.value)
            elif target.type == "domain":
                payload = await client.search_domain(target.value, category="all")
            else:
                payload = await client.search_dark_web(target.value)

            for item in _extract_items(payload):
                ext_id = _external_id(item, target)
                finding = db.scalar(select(Finding).where(Finding.tenant_id == tenant.id, Finding.external_id == ext_id))
                if finding:
                    finding.last_seen = datetime.utcnow()
                    continue

                finding = Finding(
                    tenant_id=tenant.id,
                    target_id=target.id,
                    external_id=ext_id,
                    source=item.get("source"),
                    url=item.get("url"),
                    username=item.get("username"),
                    email=item.get("email"),
                    leak_date=str(item.get("leak_date")) if item.get("leak_date") else None,
                    raw_payload=json.dumps(item, ensure_ascii=False),
                )
                db.add(finding)
                db.flush()

                alert = Alert(tenant_id=tenant.id, finding_id=finding.id, status="pending")
                db.add(alert)

                users = db.scalars(select(User).where(User.tenant_id == tenant.id)).all()
                for user in users:
                    sent = send_alert_email(
                        user.email,
                        subject=f"[DarkWatch] Novo finding para target {target.value}",
                        body=f"Novo finding detectado (external_id={ext_id}).",
                    )
                    if sent:
                        alert.status = "sent"
                        alert.sent_at = datetime.utcnow()
        run.status = "completed"
    except Exception:
        run.status = "failed"
        raise
    finally:
        run.finished_at = datetime.utcnow()
        db.commit()

    return run
