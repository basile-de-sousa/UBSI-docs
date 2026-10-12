from django.db import migrations

FORWARD = """
CREATE TRIGGER document_source_immutable BEFORE UPDATE ON documents_filerevision
FOR EACH ROW EXECUTE FUNCTION knowledge_history_immutable();
CREATE FUNCTION document_ready_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.state = 'ready' THEN RAISE EXCEPTION 'Ready preview is immutable'; END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER document_preview_immutable BEFORE UPDATE ON documents_preview
FOR EACH ROW EXECUTE FUNCTION document_ready_immutable();
CREATE FUNCTION document_content_file() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE content_kind text;
BEGIN
  SELECT kind INTO content_kind FROM knowledge_contentrecord WHERE id = NEW.record_id;
  IF NEW.file_revision_id IS NOT NULL AND (content_kind <> 'document' OR NOT EXISTS (
    SELECT 1 FROM documents_filerevision WHERE id = NEW.file_revision_id AND record_id = NEW.record_id
  )) THEN RAISE EXCEPTION 'File belongs to another document'; END IF;
  IF TG_TABLE_NAME = 'knowledge_contentrevision' AND content_kind = 'document' AND (
    NEW.file_revision_id IS NULL OR NOT EXISTS (
      SELECT 1 FROM documents_preview WHERE file_id = NEW.file_revision_id AND state = 'ready'
    )
  ) THEN RAISE EXCEPTION 'Published document needs a ready preview'; END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER document_draft_file_guard BEFORE INSERT OR UPDATE ON knowledge_contentdraft
FOR EACH ROW EXECUTE FUNCTION document_content_file();
CREATE TRIGGER document_revision_file_guard BEFORE INSERT ON knowledge_contentrevision
FOR EACH ROW EXECUTE FUNCTION document_content_file();
"""
REVERSE = """
DROP TRIGGER document_revision_file_guard ON knowledge_contentrevision;
DROP TRIGGER document_draft_file_guard ON knowledge_contentdraft;
DROP FUNCTION document_content_file();
DROP TRIGGER document_preview_immutable ON documents_preview;
DROP FUNCTION document_ready_immutable();
DROP TRIGGER document_source_immutable ON documents_filerevision;
"""


class Migration(migrations.Migration):
    dependencies = [("documents", "0001_initial"), ("knowledge", "0004_contentdraft_file_revision_and_more")]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
