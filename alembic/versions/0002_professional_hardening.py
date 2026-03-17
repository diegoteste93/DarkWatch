"""professional hardening

Revision ID: 0002_professional_hardening
Revises: 0001_init
Create Date: 2026-03-17 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_professional_hardening"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("notification_email", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("smtp_host", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("smtp_port", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("smtp_user", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("smtp_password", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("smtp_from", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("smtp_starttls", sa.Boolean(), nullable=False, server_default=sa.true()))

    op.add_column("runs", sa.Column("processed_targets", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("runs", sa.Column("successful_targets", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("runs", sa.Column("failed_targets", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("runs", sa.Column("new_findings", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("runs", sa.Column("updated_findings", sa.Integer(), nullable=False, server_default="0"))

    op.add_column("alerts", sa.Column("error", sa.String(length=255), nullable=True))

    op.create_unique_constraint("uq_target_tenant_type_value", "targets", ["tenant_id", "type", "value"])


def downgrade() -> None:
    op.drop_constraint("uq_target_tenant_type_value", "targets", type_="unique")

    op.drop_column("alerts", "error")

    op.drop_column("runs", "updated_findings")
    op.drop_column("runs", "new_findings")
    op.drop_column("runs", "failed_targets")
    op.drop_column("runs", "successful_targets")
    op.drop_column("runs", "processed_targets")

    op.drop_column("tenants", "smtp_starttls")
    op.drop_column("tenants", "smtp_from")
    op.drop_column("tenants", "smtp_password")
    op.drop_column("tenants", "smtp_user")
    op.drop_column("tenants", "smtp_port")
    op.drop_column("tenants", "smtp_host")
    op.drop_column("tenants", "notification_email")
