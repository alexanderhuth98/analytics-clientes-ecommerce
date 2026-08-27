import hashlib
import json
import os
import shutil
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests

from .config import (
    DATASET_SLUG,
    DATASET_URL,
    EXPECTED_COLUMNS,
    PUBLIC_MANIFEST_DIR,
    RAW_DIR,
    ensure_directories,
)


@dataclass(frozen=True)
class DownloadResult:
    downloaded_at: str
    dataset_slug: str
    source_url: str
    archive_path: str
    archive_bytes: int
    sha256: str
    files: list[str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_members(archive: zipfile.ZipFile, destination: Path) -> list[zipfile.ZipInfo]:
    root = destination.resolve()
    members = []
    for member in archive.infolist():
        candidate = (destination / member.filename).resolve()
        if root != candidate and root not in candidate.parents:
            raise ValueError(f"Ruta insegura dentro del ZIP: {member.filename}")
        members.append(member)
    return members


def _auth() -> tuple[str, str] | None:
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    return (username, key) if username and key else None


def download_all(force: bool = False) -> DownloadResult:
    ensure_directories()
    archive_path = RAW_DIR / "brazilian-ecommerce.zip"
    extract_dir = RAW_DIR / "olist"
    partial = archive_path.with_suffix(".zip.part")
    staging = RAW_DIR / ".olist_extracting"
    needs_download = force or not archive_path.exists()
    needs_extract = force or not extract_dir.exists()

    if needs_download:
        if partial.exists():
            partial.unlink()
        try:
            with requests.get(
                DATASET_URL,
                auth=_auth(),
                headers={"User-Agent": "analytics-clientes-ecommerce/1.0"},
                stream=True,
                timeout=(30, 180),
            ) as response:
                response.raise_for_status()
                with partial.open("wb") as target:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            target.write(chunk)
        except Exception:
            if partial.exists():
                partial.unlink()
            raise

    candidate_archive = partial if needs_download else archive_path
    if needs_extract:
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        try:
            with zipfile.ZipFile(candidate_archive) as archive:
                members = _safe_members(archive, staging)
                archive.extractall(staging, members=members)
            staged_files = sorted(path.name for path in staging.glob("*.csv"))
            missing = sorted(set(EXPECTED_COLUMNS) - set(staged_files))
            if missing:
                raise ValueError(f"El ZIP oficial no contiene los archivos esperados: {missing}")
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            if needs_download and partial.exists():
                partial.unlink()
            raise

        archive_backup = archive_path.with_suffix(".zip.backup")
        extract_backup = RAW_DIR / ".olist_backup"
        if archive_backup.exists():
            archive_backup.unlink()
        if extract_backup.exists():
            shutil.rmtree(extract_backup)
        try:
            if needs_download and archive_path.exists():
                archive_path.replace(archive_backup)
            if extract_dir.exists():
                extract_dir.replace(extract_backup)
            if needs_download:
                partial.replace(archive_path)
            staging.replace(extract_dir)
        except Exception:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            if extract_backup.exists():
                extract_backup.replace(extract_dir)
            if needs_download and archive_path.exists():
                archive_path.unlink()
            if archive_backup.exists():
                archive_backup.replace(archive_path)
            raise
        finally:
            shutil.rmtree(staging, ignore_errors=True)
            shutil.rmtree(extract_backup, ignore_errors=True)
            if archive_backup.exists():
                archive_backup.unlink()

    files = sorted(path.name for path in extract_dir.glob("*.csv"))
    missing = sorted(set(EXPECTED_COLUMNS) - set(files))
    if missing:
        raise ValueError(f"El ZIP oficial no contiene los archivos esperados: {missing}")

    result = DownloadResult(
        downloaded_at=datetime.now(UTC).isoformat(),
        dataset_slug=DATASET_SLUG,
        source_url=DATASET_URL,
        archive_path=str(archive_path.relative_to(RAW_DIR.parent)),
        archive_bytes=archive_path.stat().st_size,
        sha256=_sha256(archive_path),
        files=files,
    )
    PUBLIC_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = PUBLIC_MANIFEST_DIR / "raw_sources.jsonl"
    manifest.write_text(json.dumps(asdict(result), ensure_ascii=True) + "\n", encoding="utf-8")
    return result
