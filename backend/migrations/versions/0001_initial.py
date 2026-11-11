"""Initial normalized schema, pgvector, history trigger and analytics."""

from pathlib import Path
from alembic import op
from migrations.schema_v1 import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    Base.metadata.create_all(op.get_bind())
    sql = (Path(__file__).resolve().parents[1] / "audit_v1.sql").read_text()
    op.get_bind().exec_driver_sql(sql)


def downgrade():
    op.execute("DROP VIEW IF EXISTS job_application_counts")
    op.execute("DROP FUNCTION IF EXISTS required_skill_match(integer,integer)")
    Base.metadata.drop_all(op.get_bind())
    op.execute("DROP FUNCTION IF EXISTS audit_application_status()")
