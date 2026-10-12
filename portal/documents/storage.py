"""Private immutable objects; all delivery goes through authorized views."""
import hashlib
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_STORAGE_ROOT, file_permissions_mode=0o600, directory_permissions_mode=0o700)

    def url(self, name):
        raise NotImplementedError("Private files have no public URL.")


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def private_path(key):
    root = settings.PRIVATE_STORAGE_ROOT.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("Invalid private storage key")
    return path
