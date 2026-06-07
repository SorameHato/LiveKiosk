import hashlib
import json
from pathlib import Path


APP_DIR = Path("../src")
OUTPUT = Path("../manifest.json")

import importlib.util

spec = importlib.util.spec_from_file_location(
    "app",
    APP_DIR / "__init__.py"
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

VERSION = module.__version__


def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)

    return h.hexdigest()


manifest = {
    "version": VERSION,
    "files": {}
}

for file in APP_DIR.rglob("*"):
    if not file.is_file() or file.suffix == '.pyc':
        continue

    rel = file.relative_to(APP_DIR).as_posix()

    manifest["files"][rel] = {
        "sha256": sha256_file(file),
        "size": file.stat().st_size
    }

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("manifest.json generated")
