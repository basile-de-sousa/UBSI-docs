from django.db import migrations


def seed(apps, schema_editor):
    apps.get_model("knowledge", "ProjectState").objects.using(schema_editor.connection.alias).get_or_create(pk=1)


FORWARD = """
CREATE FUNCTION knowledge_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Published history is immutable';
END;
$$;
CREATE TRIGGER knowledge_revision_immutable BEFORE UPDATE OR DELETE ON knowledge_contentrevision
FOR EACH ROW EXECUTE FUNCTION knowledge_history_immutable();
CREATE TRIGGER knowledge_relation_immutable BEFORE UPDATE OR DELETE ON knowledge_revisionrelation
FOR EACH ROW EXECUTE FUNCTION knowledge_history_immutable();
CREATE FUNCTION knowledge_record_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND (NEW.kind <> OLD.kind OR NEW.reference <> OLD.reference OR NEW.created_by_id <> OLD.created_by_id) THEN
    RAISE EXCEPTION 'Content identity is immutable';
  END IF;
  IF NEW.current_revision_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM knowledge_contentrevision WHERE id = NEW.current_revision_id AND record_id = NEW.id
  ) THEN
    RAISE EXCEPTION 'Revision belongs to another record';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER knowledge_record_identity_guard BEFORE INSERT OR UPDATE ON knowledge_contentrecord
FOR EACH ROW EXECUTE FUNCTION knowledge_record_identity();
"""
REVERSE = """
DROP TRIGGER knowledge_record_identity_guard ON knowledge_contentrecord;
DROP FUNCTION knowledge_record_identity();
DROP TRIGGER knowledge_relation_immutable ON knowledge_revisionrelation;
DROP TRIGGER knowledge_revision_immutable ON knowledge_contentrevision;
DROP FUNCTION knowledge_history_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("knowledge", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop), migrations.RunSQL(FORWARD, REVERSE)]
