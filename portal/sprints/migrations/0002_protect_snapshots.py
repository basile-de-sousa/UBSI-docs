from django.db import migrations


FORWARD = """
CREATE TRIGGER sprint_closure_immutable BEFORE UPDATE OR DELETE ON sprints_sprintclosuresnapshot
FOR EACH ROW EXECUTE FUNCTION knowledge_history_immutable();
CREATE TRIGGER sprint_row_immutable BEFORE UPDATE OR DELETE ON sprints_sprintsnapshotrow
FOR EACH ROW EXECUTE FUNCTION knowledge_history_immutable();
CREATE TRIGGER sprint_application_immutable BEFORE UPDATE OR DELETE ON sprints_sprintsnapshotapplication
FOR EACH ROW EXECUTE FUNCTION knowledge_history_immutable();
CREATE FUNCTION sprint_active_pointer_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.active_sprint_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM knowledge_contentrecord r JOIN knowledge_contentrevision v ON v.id = r.current_revision_id
    WHERE r.id = NEW.active_sprint_id AND r.kind = 'sprint' AND r.state = 'published' AND v.payload->>'sprint_state' = 'active'
  ) THEN
    RAISE EXCEPTION 'Active sprint pointer must target a published active sprint';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER sprint_active_pointer BEFORE INSERT OR UPDATE ON knowledge_projectstate
FOR EACH ROW EXECUTE FUNCTION sprint_active_pointer_guard();
"""
REVERSE = """
DROP TRIGGER sprint_active_pointer ON knowledge_projectstate;
DROP FUNCTION sprint_active_pointer_guard();
DROP TRIGGER sprint_application_immutable ON sprints_sprintsnapshotapplication;
DROP TRIGGER sprint_row_immutable ON sprints_sprintsnapshotrow;
DROP TRIGGER sprint_closure_immutable ON sprints_sprintclosuresnapshot;
"""


class Migration(migrations.Migration):
    dependencies = [("sprints", "0001_initial"), ("knowledge", "0003_projectstate_active_sprint")]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
