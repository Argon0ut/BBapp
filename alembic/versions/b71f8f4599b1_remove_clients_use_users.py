"""remove clients and use auth users for photos

Revision ID: b71f8f4599b1
Revises: 8f3a1c2d4b9e
Create Date: 2026-04-17 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b71f8f4599b1"
down_revision: Union[str, None] = "8f3a1c2d4b9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_client_photos_photo_type"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_id"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_file_path"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_client_id"), table_name="client_photos")
    op.drop_table("client_photos")

    op.create_table(
        "client_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("photo_type", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_client_photos_file_path"), "client_photos", ["file_path"], unique=False)
    op.create_index(op.f("ix_client_photos_id"), "client_photos", ["id"], unique=False)
    op.create_index(op.f("ix_client_photos_photo_type"), "client_photos", ["photo_type"], unique=False)
    op.create_index(op.f("ix_client_photos_user_id"), "client_photos", ["user_id"], unique=False)

    op.drop_index(op.f("ix_clients_model"), table_name="clients")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_brand"), table_name="clients")
    op.drop_table("clients")


def downgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("brand", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_brand"), "clients", ["brand"], unique=False)
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(op.f("ix_clients_model"), "clients", ["model"], unique=False)

    op.drop_index(op.f("ix_client_photos_user_id"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_photo_type"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_id"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_file_path"), table_name="client_photos")
    op.drop_table("client_photos")

    op.create_table(
        "client_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("photo_type", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_client_photos_client_id"), "client_photos", ["client_id"], unique=False)
    op.create_index(op.f("ix_client_photos_file_path"), "client_photos", ["file_path"], unique=False)
    op.create_index(op.f("ix_client_photos_id"), "client_photos", ["id"], unique=False)
    op.create_index(op.f("ix_client_photos_photo_type"), "client_photos", ["photo_type"], unique=False)
