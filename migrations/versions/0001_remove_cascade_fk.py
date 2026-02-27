"""Remove ON DELETE CASCADE from FK constraints

Revision ID: 0001
Revises:
Create Date: 2026-02-27
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- departments.parent_id ---
    with op.batch_alter_table("departments") as batch_op:
        batch_op.drop_constraint("departments_parent_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "departments_parent_id_fkey",
            "departments",
            ["parent_id"],
            ["id"],
        )

    # --- employees.department_id ---
    with op.batch_alter_table("employees") as batch_op:
        batch_op.drop_constraint("employees_department_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "employees_department_id_fkey",
            "departments",
            ["department_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("employees") as batch_op:
        batch_op.drop_constraint("employees_department_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "employees_department_id_fkey",
            "departments",
            ["department_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("departments") as batch_op:
        batch_op.drop_constraint("departments_parent_id_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "departments_parent_id_fkey",
            "departments",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )
