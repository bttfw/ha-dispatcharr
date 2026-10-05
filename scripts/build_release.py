"""Build an installable ZIP from the integration files, excluding local artifacts."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "dispatcharr"
version = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf8"))["version"]
destination = ROOT / "dist"
destination.mkdir(exist_ok=True)
archive = destination / f"ha-dispatcharr-{version}.zip"
files = [
    path
    for path in COMPONENT.rglob("*")
    if path.is_file() and path.suffix in {".py", ".json", ".yaml", ".js"}
]
files.append(ROOT / "LICENSE")
with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as bundle:
    for path in sorted(files):
        bundle.write(path, path.relative_to(ROOT).as_posix())
with ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert "custom_components/dispatcharr/manifest.json" in bundle.namelist()
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf8")
print(f"{archive.name}: {len(files)} files, {archive.stat().st_size} bytes, SHA256 {digest}")
