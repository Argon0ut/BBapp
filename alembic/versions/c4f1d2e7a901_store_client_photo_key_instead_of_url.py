"""store client photo key instead of url

Revision ID: c4f1d2e7a901
Revises: b71f8f4599b1
Create Date: 2026-04-18 20:10:00.000000

"""
from typing import Sequence, Union
from pathlib import Path
from urllib.parse import urlparse

from alembic import op
import sqlalchemy as sa


revision: str = "c4f1d2e7a901"
down_revision: Union[str, None] = "b71f8f4599b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _extract_key(value: str | None) -> str | None:
    if value is None:
        return None

    raw_value = value.strip()
    if not raw_value:
        return raw_value

    if "://" not in raw_value:
        return Path(raw_value).name

    parsed = urlparse(raw_value)
    return Path(parsed.path).name


def upgrade() -> None:
    op.drop_index(op.f("ix_client_photos_file_path"), table_name="client_photos")
    op.alter_column("client_photos", "file_path", new_column_name="file_name")
    op.create_index(op.f("ix_client_photos_file_name"), "client_photos", ["file_name"], unique=False)

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, file_name FROM client_photos")).fetchall()
    for row in rows:
        normalized = _extract_key(row.file_name)
        if normalized != row.file_name:
            bind.execute(
                sa.text("UPDATE client_photos SET file_name = :file_name WHERE id = :id"),
                {"file_name": normalized, "id": row.id},
            )


def downgrade() -> None:
    op.drop_index(op.f("ix_client_photos_file_name"), table_name="client_photos")
    op.alter_column("client_photos", "file_name", new_column_name="file_path")
    op.create_index(op.f("ix_client_photos_file_path"), "client_photos", ["file_path"], unique=False)
