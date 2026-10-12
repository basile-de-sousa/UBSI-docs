import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from unittest import skipIf

from django.conf import settings
from django.test import SimpleTestCase

SPEC = importlib.util.spec_from_file_location("ubsi_operations", settings.BASE_DIR / "scripts" / "operations.py")
# The operational host script is intentionally not part of the runtime image.
if SPEC and SPEC.origin and Path(SPEC.origin).exists():
    operations = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(operations)
else:
    operations = None


@skipIf(operations is None, 'Host operations script is qualified separately from the runtime image')
class OperationsAcceptance(SimpleTestCase):
    def test_repository_backup_destination_is_refused(self):
        with self.assertRaises(operations.OperationError): operations.outside_repository(settings.BASE_DIR / "unsafe-backups")

    def test_backup_integrity_detects_corruption(self):
        with TemporaryDirectory(prefix="ubsi-m7-backup-test-") as directory:
            path = Path(directory)
            for name in operations.FILES: (path/name).write_bytes(b"fictional")
            manifest = {"format": 1, "files": {name: {"size": (path/name).stat().st_size, "sha256": operations.checksum(path/name)} for name in operations.FILES}}
            (path/"manifest.json").write_text(json.dumps(manifest))
            operations.verified(path)
            (path/"database.dump").write_bytes(b"corrupt")
            with self.assertRaises(operations.OperationError): operations.verified(path)

    def test_existing_restore_target_is_refused(self):
        from argparse import Namespace
        with patch.object(operations, "verified", return_value=(Path("/unused"), {})), patch.object(operations, "run", return_value=b"existing-volume"):
            with self.assertRaises(operations.OperationError): operations.restore(Namespace(project="ubsi-restore-existing", backup=Path("/unused")))

    def test_restore_refuses_live_project_names(self):
        from argparse import Namespace
        with patch.object(operations, "verified", return_value=(Path("/unused"), {})):
            with self.assertRaises(operations.OperationError): operations.restore(Namespace(project="ubsi-portal", backup=Path("/unused")))
