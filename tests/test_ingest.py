import csv
from pathlib import Path

import duckdb
import pytest

from ecommerce_clientes import config, ingest


@pytest.mark.parametrize(
    ("filename", "table"),
    [
        ("olist_orders_dataset.csv", "raw_orders"),
        ("olist_customers_dataset.csv", "raw_customers"),
        ("product_category_name_translation.csv", "raw_product_category_name_translation"),
    ],
)
def test_table_name_contract(filename, table):
    assert ingest._table_name(filename) == table


def test_ingest_requires_downloaded_snapshot(isolated_paths):
    with pytest.raises(FileNotFoundError, match="download"):
        ingest.ingest_all()


def test_ingest_loads_all_csv_as_varchar_and_records_state(isolated_paths, compact_snapshot):
    result = ingest.ingest_all()

    assert result.tables == 9
    assert result.rows == 37
    assert isolated_paths.database.is_file()
    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        tables = {
            row[0]
            for row in connection.execute("SHOW TABLES").fetchall()
            if row[0].startswith("raw_")
        }
        state = connection.execute("SELECT * FROM ingest_state").fetchone()
        types = connection.execute("DESCRIBE raw_order_items").fetchall()
    assert len(tables) == 9
    assert state[0] == result.ingest_run_id
    assert state[2] == config.SCHEMA_VERSION
    assert state[3:] == (9, 37)
    assert {row[1] for row in types} == {"VARCHAR"}


def test_ingest_is_idempotent_until_force_replaces_database(isolated_paths, compact_snapshot):
    first = ingest.ingest_all()
    second = ingest.ingest_all()
    forced = ingest.ingest_all(force=True)

    assert second == first
    assert forced.ingest_run_id != first.ingest_run_id
    assert forced.rows == first.rows
    assert not list(isolated_paths.warehouse.glob("*.backup"))
    assert not list(isolated_paths.warehouse.glob(".ingest-*.duckdb"))


def test_contract_mismatch_cleans_staging_and_preserves_previous_database(
    isolated_paths, compact_snapshot
):
    original = ingest.ingest_all()
    orders = compact_snapshot / "olist_orders_dataset.csv"
    rows = list(csv.reader(orders.open(encoding="utf-8", newline="")))
    rows[0][-1] = "wrong_column"
    with orders.open("w", encoding="utf-8", newline="") as target:
        csv.writer(target).writerows(rows)

    with pytest.raises(ValueError, match="Contrato incompatible en raw_orders"):
        ingest.ingest_all(force=True)

    assert not list(isolated_paths.warehouse.glob(".ingest-*.duckdb"))
    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        state = connection.execute("SELECT ingest_run_id, source_rows FROM ingest_state").fetchone()
    assert state == (original.ingest_run_id, original.rows)


def test_missing_csv_during_forced_ingest_preserves_previous_database(
    isolated_paths, compact_snapshot
):
    original = ingest.ingest_all()
    (compact_snapshot / "olist_products_dataset.csv").unlink()

    with pytest.raises(FileNotFoundError, match="olist_products_dataset.csv"):
        ingest.ingest_all(force=True)

    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        assert (
            connection.execute("SELECT ingest_run_id FROM ingest_state").fetchone()[0]
            == original.ingest_run_id
        )


def test_publish_database_restores_backup_when_replace_fails(tmp_path, monkeypatch):
    destination = tmp_path / "warehouse.duckdb"
    staging = tmp_path / "staging.duckdb"
    destination.write_text("old", encoding="utf-8")
    staging.write_text("new", encoding="utf-8")
    original_replace = Path.replace

    def fail_staging(self, target):
        if self == staging:
            raise OSError("disk failure")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", fail_staging)
    with pytest.raises(OSError, match="disk failure"):
        ingest._publish_database(staging, destination)

    assert destination.read_text(encoding="utf-8") == "old"
    assert staging.read_text(encoding="utf-8") == "new"
    assert not destination.with_suffix(".duckdb.backup").exists()


def test_publish_database_removes_stale_backup_on_success(tmp_path):
    destination = tmp_path / "warehouse.duckdb"
    staging = tmp_path / "staging.duckdb"
    backup = destination.with_suffix(".duckdb.backup")
    destination.write_text("old", encoding="utf-8")
    staging.write_text("new", encoding="utf-8")
    backup.write_text("stale", encoding="utf-8")

    ingest._publish_database(staging, destination)

    assert destination.read_text(encoding="utf-8") == "new"
    assert not staging.exists()
    assert not backup.exists()
