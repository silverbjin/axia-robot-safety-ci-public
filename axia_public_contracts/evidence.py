"""SHA256 file integrity only; not a complete scenario acceptance verifier."""
import hashlib
from pathlib import Path
import re

_SHA256 = re.compile(r'^[0-9a-f]{64}$')


def _safe_file(root, filename):
    root = Path(root).resolve()
    part = Path(filename)
    if part.is_absolute() or not part.parts or '..' in part.parts or part.as_posix() == '.':
        raise ValueError('unsafe relative path')
    target = root / part
    if target.is_symlink() or not target.resolve().is_relative_to(root):
        raise ValueError('path escapes root or is symlink')
    return target


def _digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(65536), b''):
            h.update(part)
    return h.hexdigest()


def build_manifest(root, filenames):
    manifest = {}
    for filename in filenames:
        if filename in manifest:
            raise ValueError('duplicate manifest source filename')
        path = _safe_file(root, filename)
        if not path.is_file():
            raise ValueError('manifest source file is missing: ' + filename)
        manifest[filename] = _digest(path)
    if not manifest:
        raise ValueError('empty manifest source list')
    return manifest


def verify_manifest(root, manifest, *, required_files=()):
    """Check integrity and optionally require a full named evidence set.

    A non-empty manifest is mandatory. Digest verification does not authorize
    scenario acceptance, even when all digests match.
    """
    if not isinstance(manifest, dict):
        return ['INVALID_MANIFEST']
    if not manifest:
        return ['EMPTY_MANIFEST']
    failures = []
    for filename in sorted(set(required_files)):
        try:
            _safe_file(root, filename)
        except (ValueError, TypeError):
            failures.append('UNSAFE_REQUIRED_ENTRY:' + str(filename))
            continue
        if filename not in manifest:
            failures.append('MISSING_MANIFEST_ENTRY:' + filename)
    for filename, expected in sorted(manifest.items()):
        try:
            path = _safe_file(root, filename)
        except (ValueError, TypeError):
            failures.append('UNSAFE_PATH:' + str(filename))
            continue
        if not path.is_file():
            failures.append('MISSING:' + filename)
        elif not isinstance(expected, str) or not _SHA256.fullmatch(expected):
            failures.append('INVALID_DIGEST:' + filename)
        elif _digest(path) != expected:
            failures.append('HASH_MISMATCH:' + filename)
    return failures
