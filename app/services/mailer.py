import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models import Tenant

logger = logging.getLogger(__name__)


def send_alert_email(recipient: str, subject: str, body: str, tenant: Tenant | None = None) -> bool:
    smtp_host = tenant.smtp_host if tenant and tenant.smtp_host else settings.smtp_host
    smtp_port = tenant.smtp_port if tenant and tenant.smtp_port else settings.smtp_port
    smtp_user = tenant.smtp_user if tenant and tenant.smtp_user else settings.smtp_user
    smtp_password = tenant.smtp_password if tenant and tenant.smtp_password else settings.smtp_password
    smtp_from = tenant.smtp_from if tenant and tenant.smtp_from else settings.smtp_from
    smtp_starttls = tenant.smtp_starttls if tenant else settings.smtp_starttls

    if not smtp_host:
        return False

    msg = EmailMessage()
    msg["From"] = smtp_from
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
            if smtp_starttls:
                smtp.starttls()
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
        return True
    except smtplib.SMTPException:
        logger.exception("SMTP failure recipient=%s", recipient)
        return False
