import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from conftest import write_snapshot

from ecommerce_clientes import config, download


def _zip_tree(source: Path, *, omit: str | None = None, unsafe: str | None = None) -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        for path in source.glob("*.csv"):
            if path.name != omit:
                archive.write(path, path.name)
        if unsafe:
            archive.writestr(unsafe, "not allowed")
    return payload.getvalue()


class LocalResponse:
    def __init__(self, payload: bytes, failure: Exception | None = None):
        self.payload = payload
        self.failure = failure
        self.entered = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        if self.failure:
            raise self.failure

    def iter_content(self, _chunk_size):
        midpoint = len(self.payload) // 2
        yield self.payload[:midpoint]
        yield b""
        yield self.payload[midpoint:]


def test_ensure_directories_creates_every_runtime_directory(isolated_paths):
    config.ensure_directories()

    expected = {
        isolated_paths.raw,
        isolated_paths.interim,
        isolated_paths.warehouse,
        isolated_paths.exports,
        isolated_paths.outputs,
        isolated_paths.site,
        isolated_paths.portfolio,
        isolated_paths.manifests,
    }
    assert all(path.is_dir() for path in expected)
    assert len(config.EXPECTED_COLUMNS) == 9


def test_sha256_streams_file(tmp_path):
    payload = b"abc" * 500_000
    path = tmp_path / "payload.bin"
    path.write_bytes(payload)
    assert download._sha256(path) == hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize("name", ["../escape.csv", "folder/../../escape.csv"])
def test_safe_members_rejects_zip_traversal(tmp_path, name):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(name, "bad")

    destination = tmp_path / "extract"
    with zipfile.ZipFile(archive_path) as archive, pytest.raises(ValueError, match="Ruta insegura"):
        download._safe_members(archive, destination)
    assert not (tmp_path / "escape.csv").exists()


def test_auth_requires_both_credentials(monkeypatch):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    assert download._auth() is None
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    assert download._auth() is None
    monkeypatch.setenv("KAGGLE_KEY", "secret")
    assert download._auth() == ("user", "secret")


def test_download_extracts_validates_hash_and_writes_manifest(
    isolated_paths, monkeypatch, tmp_path
):
    source = tmp_path / "zip_source"
    write_snapshot(source)
    payload = _zip_tree(source)
    response = LocalResponse(payload)
    calls = []

    def local_get(*args, **kwargs):
        calls.append((args, kwargs))
        return response

    monkeypatch.setattr(download.requests, "get", local_get)
    result = download.download_all()

    assert response.entered
    assert len(calls) == 1
    assert calls[0][0] == (config.DATASET_URL,)
    assert calls[0][1]["stream"] is True
    assert result.archive_bytes == len(payload)
    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    assert result.files == sorted(config.EXPECTED_COLUMNS)
    assert not (isolated_paths.raw / "brazilian-ecommerce.zip.part").exists()
    assert not (isolated_paths.raw / ".olist_extracting").exists()

    manifest = json.loads((isolated_paths.manifests / "raw_sources.jsonl").read_text())
    assert manifest["dataset_slug"] == config.DATASET_SLUG
    assert manifest["sha256"] == result.sha256
    assert Path(manifest["archive_path"]) == Path("raw/brazilian-ecommerce.zip")

    monkeypatch.setattr(
        download.requests,
        "get",
        lambda *_args, **_kwargs: pytest.fail("cached archive must avoid HTTP"),
    )
    cached = download.download_all()
    assert cached.sha256 == result.sha256


def test_download_force_replaces_snapshot_and_cleans_old_files(
    isolated_paths, monkeypatch, tmp_path
):
    source = tmp_path / "source"
    write_snapshot(source)
    payload = _zip_tree(source)
    monkeypatch.setattr(download.requests, "get", lambda *_a, **_k: LocalResponse(payload))
    download.download_all()
    stale = isolated_paths.raw / "olist" / "stale.csv"
    stale.write_text("old")

    download.download_all(force=True)

    assert not stale.exists()
    assert set(path.name for path in (isolated_paths.raw / "olist").glob("*.csv")) == set(
        config.EXPECTED_COLUMNS
    )


def test_download_rejects_missing_contract_file(isolated_paths, monkeypatch, tmp_path):
    source = tmp_path / "source"
    write_snapshot(source)
    missing = "olist_sellers_dataset.csv"
    payload = _zip_tree(source, omit=missing)
    monkeypatch.setattr(download.requests, "get", lambda *_a, **_k: LocalResponse(payload))

    with pytest.raises(ValueError, match=missing):
        download.download_all()


def test_forced_download_keeps_previous_snapshot_when_new_zip_is_incomplete(
    isolated_paths, monkeypatch, tmp_path
):
    previous = isolated_paths.raw / "olist"
    write_snapshot(previous)
    old_seller = (previous / "olist_sellers_dataset.csv").read_bytes()
    source = tmp_path / "incomplete"
    write_snapshot(source)
    payload = _zip_tree(source, omit="olist_sellers_dataset.csv")
    monkeypatch.setattr(download.requests, "get", lambda *_a, **_k: LocalResponse(payload))

    with pytest.raises(ValueError, match="olist_sellers_dataset.csv"):
        download.download_all(force=True)

    assert (previous / "olist_sellers_dataset.csv").read_bytes() == old_seller


def test_download_rejects_unsafe_archive_without_writing_outside(
    isolated_paths, monkeypatch, tmp_path
):
    source = tmp_path / "source"
    write_snapshot(source)
    payload = _zip_tree(source, unsafe="../owned.txt")
    monkeypatch.setattr(download.requests, "get", lambda *_a, **_k: LocalResponse(payload))

    with pytest.raises(ValueError, match="Ruta insegura"):
        download.download_all()
    assert not (isolated_paths.raw / "owned.txt").exists()
    assert not (isolated_paths.raw / "olist").exists()


def test_failed_forced_download_preserves_published_archive(isolated_paths, monkeypatch):
    config.ensure_directories()
    archive = isolated_paths.raw / "brazilian-ecommerce.zip"
    archive.write_bytes(b"known-good")
    failure = RuntimeError("HTTP failed")
    monkeypatch.setattr(
        download.requests, "get", lambda *_a, **_k: LocalResponse(b"partial", failure)
    )

    with pytest.raises(RuntimeError, match="HTTP failed"):
        download.download_all(force=True)
    assert archive.read_bytes() == b"known-good"
