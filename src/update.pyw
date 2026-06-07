import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import traceback
import urllib.request
from datetime import datetime

repo_dir = pathlib.Path(__file__).resolve().parent.parent
src_dir = repo_dir / 'src'
manifest_path = repo_dir / 'manifest.json'
log_path = pathlib.Path(os.environ.get('APPDATA', '')) / 'SkyWare' / 'LiveKiosk' / 'update.log'

RELEASE_BRANCHES = frozenset({'candy', 'lily'})
REMOTE_REPO = 'SorameHato/LiveKiosk'
REMOTE_BASE = f'https://raw.githubusercontent.com/{REMOTE_REPO}'
HTTP_TIMEOUT = 60
HTTP_HEADERS = {'User-Agent': 'LiveKiosk-Updater'}


def log(message: str) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now().isoformat()} {message}\n')
    except Exception:
        pass


def load_version_branch() -> str:
    spec = importlib.util.spec_from_file_location('lk_meta', src_dir / '__init__.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.version_branch


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return json.loads(response.read().decode('utf-8'))


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return response.read()


def update_via_manifest(branch: str) -> None:
    remote_manifest = fetch_json(f'{REMOTE_BASE}/{branch}/manifest.json')
    pending = []

    for rel_path, meta in remote_manifest.get('files', {}).items():
        local_file = src_dir / rel_path.replace('/', os.sep)
        expected = meta['sha256']
        if local_file.is_file() and sha256_file(local_file) == expected:
            continue

        data = fetch_bytes(f'{REMOTE_BASE}/{branch}/src/{rel_path}')
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'SHA256 mismatch for {rel_path}')

        pending.append((local_file, data))

    if not pending:
        if not manifest_path.is_file():
            manifest_path.write_text(json.dumps(remote_manifest, indent=2) + '\n', encoding='utf-8')
        log(f'manifest update: already up to date ({remote_manifest.get("version")})')
        return

    for local_file, data in pending:
        local_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = local_file.with_suffix(local_file.suffix + '.tmp')
        tmp.write_bytes(data)
        tmp.replace(local_file)

    manifest_path.write_text(json.dumps(remote_manifest, indent=2) + '\n', encoding='utf-8')
    log(f'manifest update OK -> {remote_manifest.get("version")} ({len(pending)} files)')


def update_via_git() -> None:
    git_dir = repo_dir / 'git' / 'cmd' / 'git.exe'
    os.environ['GIT_PYTHON_GIT_EXECUTABLE'] = str(git_dir)

    import git

    repo = git.Repo(str(repo_dir))
    origin = repo.remotes.origin
    origin.fetch()

    branch_name = repo.active_branch.name
    local_commit = repo.active_branch.commit
    remote_commit = origin.refs[branch_name].commit

    if local_commit == remote_commit:
        log('git update: already up to date')
        return

    if not repo.is_ancestor(local_commit, remote_commit):
        log('git update: skipped (not fast-forward)')
        return

    origin.pull()
    log(f'git update OK -> {remote_commit.hexsha[:8]}')


version_branch = load_version_branch()

try:
    if version_branch in RELEASE_BRANCHES:
        update_via_manifest(version_branch)
    else:
        update_via_git()
except Exception as exc:
    log(f'update failed: {exc}\n{traceback.format_exc()}')

BASE_DIR = str(src_dir)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from init import main

main()
