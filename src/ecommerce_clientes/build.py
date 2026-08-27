import uuid
from dataclasses import dataclass
from datetime import date

import duckdb

from .config import DATABASE_PATH, DUCKDB_THREADS, SCHEMA_VERSION, SEGMENTATION_VERSION, SQL_DIR


@dataclass(frozen=True)
class BuildResult:
    build_id: str
    as_of_date: date
    tables_built: int


def _sql_files() -> list[str]:
    return ["01_schema.sql", "02_marts.sql", "03_quality_checks.sql"]


def build_analytics(as_of: date | None = None) -> BuildResult:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError("No existe el warehouse. Ejecute primero ingest.")
    build_id = str(uuid.uuid4())
    with duckdb.connect(str(DATABASE_PATH)) as connection:
        connection.execute(f"SET threads = {DUCKDB_THREADS}")
        max_date = connection.execute(
            "SELECT MAX(TRY_CAST(order_purchase_timestamp AS TIMESTAMP)::DATE) FROM raw_orders"
        ).fetchone()[0]
        effective_date = as_of or max_date
        if effective_date is None:
            raise ValueError("No se pudo determinar la fecha de corte.")
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("DROP TABLE IF EXISTS build_context")
            connection.execute(
                """
                CREATE TABLE build_context AS
                SELECT ?::VARCHAR AS build_id,
                       ?::DATE AS as_of_date,
                       ?::VARCHAR AS schema_version,
                       ?::VARCHAR AS segmentation_version,
                       current_timestamp AS built_at
                """,
                [build_id, effective_date, SCHEMA_VERSION, SEGMENTATION_VERSION],
            )
            for filename in _sql_files():
                connection.execute((SQL_DIR / filename).read_text(encoding="utf-8"))
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        tables = connection.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchone()[0]
    return BuildResult(build_id, effective_date, tables)
