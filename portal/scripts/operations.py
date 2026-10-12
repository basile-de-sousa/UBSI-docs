#!/usr/bin/env python3
"""Private, quiesced Compose backups and restores into fresh isolated projects."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time

REPOSITORY = Path(__file__).resolve().parents[2]
FILES = ("database.dump", "private.tar", "audit.json")

# Static code only: secrets and uploaded names never become command text.
PACK = """
import os, pathlib, sys, tarfile
root = pathlib.Path(os.environ['PRIVATE_STORAGE_ROOT'])
for path in root.rglob('*'):
    if path.is_symlink() or not (path.is_file() or path.is_dir()): raise SystemExit(1)
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
    archive.add(root, arcname='private', recursive=True)
"""
UNPACK = """
import os, pathlib, shutil, sys, tarfile
root = pathlib.Path(os.environ['PRIVATE_STORAGE_ROOT']).resolve()
if any(root.iterdir()): raise SystemExit(1)
with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') as archive:
    for entry in archive:
        name = pathlib.PurePosixPath(entry.name)
        if name.is_absolute() or not name.parts or name.parts[0] != 'private' or '..' in name.parts or not (entry.isdir() or entry.isfile()): raise SystemExit(1)
        target = root.joinpath(*name.parts[1:])
        if entry.isdir(): target.mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open('xb') as output: shutil.copyfileobj(archive.extractfile(entry), output)
            target.chmod(0o600)
        os.chown(target, 10001, 10001)
root.chmod(0o700)
os.chown(root, 10001, 10001)
"""


class OperationError(Exception):
    pass


def run(args, *, output=None, source=None):
    result = subprocess.run(args, stdin=source or subprocess.DEVNULL, stdout=output or subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode: raise OperationError("Command failed; credentials and raw tool diagnostics suppressed.")
    return result.stdout


def checksum(path):
    with path.open('rb') as source: return hashlib.file_digest(source, 'sha256').hexdigest()


def outside_repository(path):
    path = path.expanduser().resolve()
    if path.is_relative_to(REPOSITORY) or REPOSITORY.is_relative_to(path): raise OperationError("Backup destination must be outside the repository and its parents.")
    return path


def compose(options, project=None, extra=None):
    command = ['docker', 'compose', '--project-name', project or options.project]
    if options.env_file: command += ['--env-file', str(options.env_file.resolve())]
    for path in options.compose: command += ['-f', str(path.resolve())]
    if extra: command += ['-f', str(extra)]
    return command


def app(command, *args, root=False):
    return command + ['run', '--rm', '-T', '--no-deps', '--entrypoint', 'python', *( ['--user', '0'] if root else []), 'web', *args]


def verified(path):
    if path.is_symlink(): raise OperationError('Symlinked backup is refused.')
    path = outside_repository(path)
    try:
        manifest = json.loads((path/'manifest.json').read_text())
        if manifest['format'] != 1 or set(manifest['files']) != set(FILES): raise ValueError
        for name in FILES:
            file = path/name
            if file.is_symlink() or not file.is_file() or file.stat().st_size != manifest['files'][name]['size'] or checksum(file) != manifest['files'][name]['sha256']: raise ValueError
    except (OSError, ValueError, KeyError, TypeError): raise OperationError('Backup manifest or artifact integrity failed.') from None
    return path, manifest


def backup(options):
    target = outside_repository(options.destination)
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.stat().st_mode & 0o077: raise OperationError('Backup root must have mode 700.')
    command = compose(options)
    services = run(command + ['ps', '--status', 'running', '--services']).decode().splitlines()
    if 'db' not in services or 'migrate' in services: raise OperationError('Database must be running and migrations must be stopped.')
    resume = [service for service in ('web', 'worker') if service in services]
    path = target/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(4))
    path.mkdir(mode=0o700)
    started = time.monotonic()
    try:
        run(command+['stop', 'web', 'worker'])
        with (path/'database.dump').open('xb') as output:
            run(command+['exec', '-T', 'db', 'sh', '-c', 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl'], output=output)
        with (path/'private.tar').open('xb') as output: run(app(command, '-c', PACK, root=True), output=output)
        audit = run(app(command, 'manage.py', 'audit_portal'))
        (path/'audit.json').write_bytes(audit)
        image = run(command+['images', '-q', 'web']).decode().strip().splitlines()
        manifest = {'format': 1, 'created_at': datetime.now(timezone.utc).isoformat(), 'tier': options.tier, 'image': image[0] if image else None, 'files': {name: {'sha256': checksum(path/name), 'size': (path/name).stat().st_size} for name in FILES}, 'quiesced_seconds': round(time.monotonic()-started, 3)}
        (path/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        for item in path.iterdir(): item.chmod(0o600)
        print(json.dumps({'backup': str(path), 'tier': options.tier, 'seconds': manifest['quiesced_seconds']}))
    finally:
        if resume: run(command+['start', *resume])
    # An incomplete directory intentionally has no valid manifest and is never restorable.


def restore(options):
    path, manifest = verified(options.backup)
    if not re.fullmatch(r'ubsi-restore-[a-z0-9-]{1,48}', options.project): raise OperationError('Restore requires a new ubsi-restore-* project.')
    for kind in ['container', 'volume', 'network']:
        if run(['docker', kind, 'ls', *(['--all'] if kind == 'container' else []), '-q', '--filter', 'label=com.docker.compose.project='+options.project]).strip(): raise OperationError('Restore target already exists; live overwrite is forbidden.')
    configuration = json.loads(run(compose(options)+['config', '--format', 'json']))
    configured_image = configuration['services']['web']['image']
    actual_image = run(['docker', 'image', 'inspect', configured_image, '--format', '{{.Id}}']).decode().strip().removeprefix('sha256:')
    if actual_image != str(manifest.get('image', '')).removeprefix('sha256:'): raise OperationError('Restore requires the exact backed-up application image already available locally.')
    started = time.monotonic()
    # No published ports, outbound account delivery, worker, or reader activation.
    override = 'services:\n  db:\n    ports: !reset []\n  web:\n    ports: !reset []\n    environment:\n      PORTAL_ENV: development\n      DEBUG: "false"\n      PUBLIC_BASE_URL: http://127.0.0.1:8000\n      ALLOWED_HOSTS: localhost,127.0.0.1\n      CSRF_TRUSTED_ORIGINS: ""\n      TRUST_HTTPS_PROXY: "false"\n      TRUSTED_PROXY_CIDRS: ""\n      EMAIL_HOST: ""\n      EMAIL_HOST_USER: ""\n      EMAIL_HOST_PASSWORD: ""\n      CHATBOT_QUALIFICATION_FILE: ""\n'
    with tempfile.TemporaryDirectory(prefix='ubsi-restore-config-') as temporary:
        config = Path(temporary)/'restore.yaml'
        config.write_text(override)
        command = compose(options, extra=config)
        try:
            run(command+['up', '-d', '--wait', '--no-deps', 'db'])
            with (path/'database.dump').open('rb') as source:
                run(command+['exec', '-T', 'db', 'sh', '-c', 'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --exit-on-error --no-owner --no-acl'], source=source)
            with (path/'private.tar').open('rb') as source: run(app(command, '-c', UNPACK, root=True), source=source)
            audit = json.loads(run(app(command, 'manage.py', 'audit_portal')))
            original = json.loads((path/'audit.json').read_text())
            for key in ['counts', 'inventory', 'migrations', 'database_fingerprint']:
                if audit[key] != original[key]: raise OperationError('Restored consistency inventory does not match the backup.')
            print(json.dumps({'restored': True, 'project': options.project, 'seconds': round(time.monotonic()-started, 3), 'counts': audit['counts'], 'migrations': audit['migrations'], 'inventory_matches': True, 'database_fingerprints_match': True, 'source_image': manifest.get('image'), 'chatbot_qualified': audit['chatbot_qualified']}))
        finally:
            # Keep recoverable volumes, but never leave a rehearsal running.
            run(command+['down'])


def retention(options):
    root = outside_repository(options.destination)
    rows = []
    for path in root.iterdir():
        if not path.is_dir(): continue
        try: _, manifest = verified(path)
        except OperationError: continue
        rows.append((path, manifest))
    keep = set()
    for tier, limit in [('daily', 7), ('weekly', 4)]:
        candidates = sorted((row for row in rows if row[1]['tier'] == tier), key=lambda row: row[1]['created_at'], reverse=True)
        keep.update(row[0] for row in candidates[:limit])
    print(json.dumps({'keep': [str(path) for path, _ in rows if path in keep], 'expired_candidates': [str(path) for path, _ in rows if path not in keep], 'deleted': 0}))


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--compose', action='append', type=Path, required=True)
    parser.add_argument('--env-file', type=Path)
    sub = parser.add_subparsers(dest='operation', required=True)
    create = sub.add_parser('backup')
    create.add_argument('--destination', type=Path, required=True)
    create.add_argument('--tier', choices=['daily', 'weekly'], default='daily')
    recover = sub.add_parser('restore')
    recover.add_argument('--backup', type=Path, required=True)
    verify = sub.add_parser('verify')
    verify.add_argument('--backup', type=Path, required=True)
    retain = sub.add_parser('retention')
    retain.add_argument('--destination', type=Path, required=True)
    options = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,62}', options.project): parser.error('Invalid project name.')
    try:
        if options.operation == 'backup': backup(options)
        elif options.operation == 'restore': restore(options)
        elif options.operation == 'verify': verified(options.backup); print('{"verified":true}')
        else: retention(options)
    except OperationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError):
        print('Operation failed; no private diagnostics emitted. Check prerequisites and artifact integrity.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
