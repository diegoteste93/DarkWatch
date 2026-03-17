import hashlib
import json
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.leakradar_client import LeakRadarClient
from app.models import Alert, Finding, Run, Target, Tenant, User
from app.services.mailer import send_alert_email

logger = logging.getLogger(__name__)


RUNNING_STATUSES = {"pending", "running"}


def _extract_items(payload: dict) -> list[dict]:
    for key in ("results", "items", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            return [i for i in value if isinstance(i, dict)]
    return []


def _normalize_item(item: dict) -> dict:
    return {
        "source": str(item.get("source") or "unknown"),
        "url": str(item.get("url") or ""),
        "username": str(item.get("username") or ""),
        "email": str(item.get("email") or "").lower() or None,
        "leak_date": str(item.get("leak_date") or item.get("date") or "unknown"),
    }


def _external_id(item: dict, target: Target) -> str:
    if item.get("id"):
        return str(item["id"])
    normalized = _normalize_item(item)
    basis = "|".join(
        [
            target.type,
            target.value,
            normalized["url"],
            normalized["username"] or (normalized["email"] or ""),
            normalized["source"],
            normalized["leak_date"],
        ]
    )
    return hashlib.sha256(basis.encode()).hexdigest()


async def scan_tenant(db: Session, tenant: Tenant, trigger_type: str = "scheduled") -> Run:
    running = db.scalar(
        select(Run).where(Run.tenant_id == tenant.id, Run.status.in_(list(RUNNING_STATUSES))).order_by(Run.id.desc())
    )
    if running:
        return running

    run = Run(tenant_id=tenant.id, trigger_type=trigger_type, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    client = LeakRadarClient(settings.leakradar_api_key, settings.leakradar_base_url)
    targets = db.scalars(select(Target).where(Target.tenant_id == tenant.id, Target.active.is_(True))).all()

    for target in targets:
        run.processed_targets += 1
        try:
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
                    run.updated_findings += 1
                    continue

                normalized = _normalize_item(item)
                finding = Finding(
                    tenant_id=tenant.id,
                    target_id=target.id,
                    external_id=ext_id,
                    source=normalized["source"],
                    url=normalized["url"] or None,
                    username=normalized["username"] or None,
                    email=normalized["email"],
                    leak_date=normalized["leak_date"],
                    raw_payload=json.dumps(item, ensure_ascii=False),
                )
                db.add(finding)
                db.flush()
                run.new_findings += 1

                alert = Alert(tenant_id=tenant.id, finding_id=finding.id, status="pending")
                db.add(alert)

                recipients = []
                if tenant.notification_email:
                    recipients.append(tenant.notification_email)
                else:
                    recipients.extend([u.email for u in db.scalars(select(User).where(User.tenant_id == tenant.id)).all()])

                for recipient in recipients:
                    sent = send_alert_email(
                        recipient,
                        subject=f"[DarkWatch] Novo finding para target {target.value}",
                        body=f"Novo finding detectado (external_id={ext_id}).",
                        tenant=tenant,
                    )
                    if sent:
                        alert.status = "sent"
                        alert.sent_at = datetime.utcnow()
                    else:
                        alert.status = "failed"
                        alert.error = "SMTP_FAILURE"
            run.successful_targets += 1
        except Exception:
            logger.exception("scan target failed tenant_id=%s run_id=%s target_id=%s", tenant.id, run.id, target.id)
            run.failed_targets += 1
            continue

    if run.failed_targets == 0:
        run.status = "completed"
    elif run.successful_targets == 0:
        run.status = "failed"
    else:
        run.status = "partial_failed"

    run.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(run)
    return run
