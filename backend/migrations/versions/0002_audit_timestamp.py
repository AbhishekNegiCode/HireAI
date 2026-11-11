"""Maintain timestamps for direct SQL status transitions as well as ORM writes."""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE OR REPLACE FUNCTION audit_application_status() RETURNS trigger AS $$
    BEGIN
      IF TG_OP = 'INSERT' THEN
        INSERT INTO application_status_history(application_id, old_status, new_status, changed_by)
        VALUES (NEW.application_id, NULL, NEW.status, NULLIF(current_setting('app.user_id', true), '')::integer);
      ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO application_status_history(application_id, old_status, new_status, changed_by)
        VALUES (NEW.application_id, OLD.status, NEW.status, NULLIF(current_setting('app.user_id', true), '')::integer);
        UPDATE applications SET updated_at = CURRENT_TIMESTAMP WHERE application_id = NEW.application_id;
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql"""
    )


def downgrade():
    # Keeping a more accurate timestamp is safe when downgrading this fix.
    pass
