import csv
from dataclasses import dataclass
from pathlib import Path

import pytest

from ecommerce_clientes import build, config, download, export, ingest, validate


@dataclass(frozen=True)
class IsolatedPaths:
    root: Path
    data: Path
    raw: Path
    interim: Path
    warehouse: Path
    exports: Path
    database: Path
    outputs: Path
    site: Path
    portfolio: Path
    manifests: Path


@pytest.fixture
def isolated_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> IsolatedPaths:
    root = tmp_path / "project"
    data = root / "data"
    paths = IsolatedPaths(
        root=root,
        data=data,
        raw=data / "raw",
        interim=data / "interim",
        warehouse=data / "warehouse",
        exports=data / "exports",
        database=data / "warehouse" / "ecommerce.duckdb",
        outputs=root / "outputs",
        site=root / "site",
        portfolio=root / "portfolio_data",
        manifests=root / "manifests",
    )

    config_values = {
        "PROJECT_ROOT": paths.root,
        "DATA_DIR": paths.data,
        "RAW_DIR": paths.raw,
        "INTERIM_DIR": paths.interim,
        "WAREHOUSE_DIR": paths.warehouse,
        "EXPORT_DIR": paths.exports,
        "DATABASE_PATH": paths.database,
        "OUTPUT_DIR": paths.outputs,
        "SITE_DIR": paths.site,
        "PORTFOLIO_DATA_DIR": paths.portfolio,
        "PUBLIC_MANIFEST_DIR": paths.manifests,
    }
    for name, value in config_values.items():
        monkeypatch.setattr(config, name, value)

    monkeypatch.setattr(download, "RAW_DIR", paths.raw)
    monkeypatch.setattr(download, "PUBLIC_MANIFEST_DIR", paths.manifests)
    monkeypatch.setattr(ingest, "RAW_DIR", paths.raw)
    monkeypatch.setattr(ingest, "WAREHOUSE_DIR", paths.warehouse)
    monkeypatch.setattr(ingest, "DATABASE_PATH", paths.database)
    monkeypatch.setattr(build, "DATABASE_PATH", paths.database)
    monkeypatch.setattr(validate, "DATABASE_PATH", paths.database)
    monkeypatch.setattr(validate, "OUTPUT_DIR", paths.outputs)
    monkeypatch.setattr(validate, "PROJECT_ROOT", paths.root)
    monkeypatch.setattr(export, "DATABASE_PATH", paths.database)
    monkeypatch.setattr(export, "EXPORT_DIR", paths.exports)
    monkeypatch.setattr(export, "OUTPUT_DIR", paths.outputs)
    monkeypatch.setattr(export, "PORTFOLIO_DATA_DIR", paths.portfolio)
    monkeypatch.setattr(export, "PROJECT_ROOT", paths.root)
    monkeypatch.setattr(export, "SITE_DIR", paths.site)
    return paths


def _compact_rows() -> dict[str, list[list[object]]]:
    return {
        "olist_customers_dataset.csv": [
            ["c_a", "u_a", 1000, "sao paulo", "sp"],
            ["c_b", "u_b", 1000, "sao paulo", "sp"],
            ["c_c", "u_c", 2000, "rio", "rj"],
            ["c_zero", "u_zero", 2000, "rio", "rj"],
        ],
        "olist_geolocation_dataset.csv": [
            [1000, -23.5, -46.6, "sao paulo", "sp"],
            [1000, -23.6, -46.7, "sao paulo", "SP"],
            [2000, -22.9, -43.2, "rio", "rj"],
        ],
        "olist_order_items_dataset.csv": [
            ["o_a", 1, "p_home", "s_1", "2018-01-03 00:00:00", 800, 5],
            ["o_b", 1, "p_home", "s_1", "2018-01-04 00:00:00", 75, 1],
            ["o_b", 2, "p_books", "s_1", "2018-01-04 00:00:00", 75, 1],
            ["o_c", 1, "p_home", "s_1", "2018-02-03 00:00:00", 10, 1],
            ["o_c", 2, "p_books", "s_1", "2018-02-03 00:00:00", 10, 1],
            ["o_c", 3, "p_toys", "s_1", "2018-02-03 00:00:00", 10, 1],
            ["o_c", 4, "p_toys", "s_1", "2018-02-03 00:00:00", 10, 1],
            ["o_zero", 1, "p_unknown", "s_1", "2018-02-04 00:00:00", 0, 0],
        ],
        "olist_order_payments_dataset.csv": [
            ["o_a", 1, "credit_card", 1, 805],
            ["o_b", 1, "voucher", 1, 100],
            ["o_b", 2, "credit_card", 2, 52],
            ["o_c", 1, "credit_card", 1, 44],
            ["o_zero", 1, "voucher", 1, 0],
        ],
        "olist_order_reviews_dataset.csv": [
            ["r_a", "o_a", 5, "ok", "great", "2018-01-05", "2018-01-06"],
            ["r_b1", "o_b", 1, "late", "late", "2018-01-09", "2018-01-10"],
            ["r_b2", "o_b", 3, "", "second", "2018-01-09", "2018-01-11"],
            ["r_c", "o_c", 4, "ok", "fine", "2018-02-05", "2018-02-06"],
            ["r_zero", "o_zero", 5, "", "", "2018-02-06", "2018-02-07"],
        ],
        "olist_orders_dataset.csv": [
            [
                "o_a",
                "c_a",
                "delivered",
                "2018-01-01",
                "2018-01-01 01:00:00",
                "2018-01-02",
                "2018-01-04",
                "2018-01-05",
            ],
            [
                "o_b",
                "c_b",
                "delivered",
                "2018-01-02",
                "2018-01-02 01:00:00",
                "2018-01-03",
                "2018-01-08",
                "2018-01-06",
            ],
            [
                "o_c",
                "c_c",
                "delivered",
                "2018-02-01",
                "2018-02-01 01:00:00",
                "2018-02-02",
                "2018-02-04",
                "2018-02-05",
            ],
            [
                "o_zero",
                "c_zero",
                "delivered",
                "2018-02-02",
                "2018-02-02 01:00:00",
                "2018-02-03",
                "2018-02-05",
                "2018-02-06",
            ],
        ],
        "olist_products_dataset.csv": [
            ["p_home", "casa", 10, 20, 1, 100, 10, 10, 10],
            ["p_books", "livros", 10, 20, 1, 200, 20, 10, 10],
            ["p_toys", "brinquedos", 10, 20, 2, 300, 20, 20, 10],
            ["p_unknown", "sem_traducao", 5, 5, 0, 50, 5, 5, 5],
        ],
        "olist_sellers_dataset.csv": [["s_1", 1000, "sao paulo", "sp"]],
        "product_category_name_translation.csv": [
            ["casa", "home"],
            ["livros", "books"],
            ["brinquedos", "toys"],
        ],
    }


def _publishable_rows() -> dict[str, list[list[object]]]:
    rows = {name: [] for name in config.EXPECTED_COLUMNS}
    rows["olist_customers_dataset.csv"] = [["c_bulk", "u_bulk", 1000, "city", "sp"]]
    rows["olist_geolocation_dataset.csv"] = [[1000, -23.5, -46.6, "city", "sp"]]
    rows["olist_products_dataset.csv"] = [["p_bulk", "casa", 10, 20, 1, 100, 10, 10, 10]]
    rows["olist_sellers_dataset.csv"] = [["s_bulk", 1000, "city", "sp"]]
    rows["product_category_name_translation.csv"] = [["casa", "home"]]
    for index in range(60):
        order_id = f"o_{index:02d}"
        late = index >= 30
        delivered = "2018-01-08" if late else "2018-01-04"
        estimated = "2018-01-06" if late else "2018-01-05"
        rows["olist_orders_dataset.csv"].append(
            [
                order_id,
                "c_bulk",
                "delivered",
                "2018-01-01",
                "2018-01-01 01:00:00",
                "2018-01-02",
                delivered,
                estimated,
            ]
        )
        rows["olist_order_items_dataset.csv"].append(
            [order_id, 1, "p_bulk", "s_bulk", "2018-01-03", 10 + index, 1]
        )
        rows["olist_order_payments_dataset.csv"].append([order_id, 1, "credit_card", 1, 11 + index])
        rows["olist_order_reviews_dataset.csv"].append(
            [
                f"r_{index:02d}",
                order_id,
                2 if late else 5,
                "",
                "",
                "2018-01-09",
                "2018-01-10",
            ]
        )
    return rows


def write_snapshot(source_dir: Path, mode: str = "compact") -> dict[str, list[list[object]]]:
    rows = _compact_rows() if mode == "compact" else _publishable_rows()
    source_dir.mkdir(parents=True, exist_ok=True)
    for filename, columns in config.EXPECTED_COLUMNS.items():
        with (source_dir / filename).open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(columns)
            writer.writerows(rows[filename])
    return rows


@pytest.fixture
def snapshot_factory(isolated_paths: IsolatedPaths):
    def create(mode: str = "compact") -> Path:
        source = isolated_paths.raw / "olist"
        write_snapshot(source, mode)
        return source

    return create


@pytest.fixture
def compact_snapshot(snapshot_factory) -> Path:
    return snapshot_factory("compact")


@pytest.fixture
def built_compact(compact_snapshot: Path):
    ingest_result = ingest.ingest_all()
    build_result = build.build_analytics()
    return ingest_result, build_result
