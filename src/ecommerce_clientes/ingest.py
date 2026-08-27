import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from .config import (
    DATABASE_PATH,
    DUCKDB_THREADS,
    EXPECTED_COLUMNS,
    RAW_DIR,
    SCHEMA_VERSION,
    WAREHOUSE_DIR,
    ensure_directories,
)


@dataclass(frozen=True)
class IngestResult:
    ingest_run_id: str
    tables: int
    rows: int


def _table_name(filename: str) -> str:
    return "raw_" + filename.removeprefix("olist_").removesuffix("_dataset.csv").removesuffix(
        ".csv"
    )


def _validate_columns(
    connection: duckdb.DuckDBPyConnection, table: str, expected: list[str]
) -> None:
    actual = [row[0] for row in connection.execute(f"DESCRIBE {table}").fetchall()]
    if actual != expected:
        raise ValueError(
            f"Contrato incompatible en {table}: esperado={expected}, recibido={actual}"
        )


def _publish_database(staging: Path, destination: Path) -> None:
    backup = destination.with_suffix(".duckdb.backup")
    if backup.exists():
        backup.unlink()
    if destination.exists():
        destination.replace(backup)
    try:
        staging.replace(destination)
    except Exception:
        if backup.exists():
            backup.replace(destination)
        raise
    if backup.exists():
        backup.unlink()


def ingest_all(force: bool = False) -> IngestResult:
    ensure_directories()
    source_dir = RAW_DIR / "olist"
    if not source_dir.exists():
        raise FileNotFoundError("No existe el snapshot Olist. Ejecute primero download.")
    if DATABASE_PATH.exists() and not force:
        with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
            state = connection.execute(
                "SELECT ingest_run_id, source_tables, source_rows FROM ingest_state"
            ).fetchone()
        return IngestResult(state[0], state[1], state[2])

    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())
    staging = WAREHOUSE_DIR / f".ingest-{run_id}.duckdb"
    if staging.exists():
        staging.unlink()
    total_rows = 0
    try:
        with duckdb.connect(str(staging)) as connection:
            connection.execute(f"SET threads = {DUCKDB_THREADS}")
            connection.execute("BEGIN TRANSACTION")
            for filename, expected in EXPECTED_COLUMNS.items():
                source = source_dir / filename
                if not source.exists():
                    raise FileNotFoundError(f"Falta la fuente requerida: {filename}")
                table = _table_name(filename)
                connection.execute(
                    f"CREATE TABLE {table} AS SELECT * FROM read_csv(?, header=true, "
                    "all_varchar=true, sample_size=-1, strict_mode=true)",
                    [str(source)],
                )
                _validate_columns(connection, table, expected)
                total_rows += connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            connection.execute(
                """
                CREATE TABLE ingest_state AS
                SELECT ?::VARCHAR AS ingest_run_id,
                       ?::TIMESTAMPTZ AS ingested_at,
                       ?::VARCHAR AS schema_version,
                       ?::INTEGER AS source_tables,
                       ?::BIGINT AS source_rows
                """,
                [
                    run_id,
                    datetime.now(UTC),
                    SCHEMA_VERSION,
                    len(EXPECTED_COLUMNS),
                    total_rows,
                ],
            )
            connection.execute("COMMIT")
        _publish_database(staging, DATABASE_PATH)
    except Exception:
        if staging.exists():
            staging.unlink()
        raise
    return IngestResult(run_id, len(EXPECTED_COLUMNS), total_rows)
