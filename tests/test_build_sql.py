from datetime import date

import duckdb
import pytest

from ecommerce_clientes import build, config, ingest


def _fetch_map(connection, sql: str) -> dict:
    return dict(connection.execute(sql).fetchall())


def test_build_requires_ingested_warehouse(isolated_paths):
    with pytest.raises(FileNotFoundError, match="ingest"):
        build.build_analytics()


def test_build_rejects_warehouse_without_purchase_dates(isolated_paths):
    isolated_paths.warehouse.mkdir(parents=True)
    with duckdb.connect(str(isolated_paths.database)) as connection:
        connection.execute("CREATE TABLE raw_orders(order_purchase_timestamp VARCHAR)")

    with pytest.raises(ValueError, match="fecha de corte"):
        build.build_analytics()


def test_build_executes_production_sql_and_applies_segmentation_rules(
    isolated_paths, built_compact
):
    ingest_result, result = built_compact

    assert result.as_of_date == date(2018, 2, 2)
    assert result.tables_built > ingest_result.tables
    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        segments = connection.execute(
            """
            SELECT customer_unique_id, value_segment, unit_segment, category_segment,
                   coverage_status, merchandise_gmv_brl
            FROM mart_customer_segmentation_asof
            ORDER BY customer_unique_id
            """
        ).fetchall()
        context = connection.execute(
            "SELECT build_id, as_of_date, schema_version, segmentation_version FROM build_context"
        ).fetchone()
        geography = connection.execute(
            "SELECT latitude, longitude, state, source_points FROM dim_geography WHERE zip_code_prefix=1000"
        ).fetchone()

    assert segments == [
        ("u_a", "A_HIGH_VALUE", "ONE_ITEM", "SPECIALIST", "PUBLISHABLE", 800),
        ("u_b", "B_MEDIUM_VALUE", "TWO_TO_THREE", "MIXED", "PUBLISHABLE", 150),
        ("u_c", "C_LOW_VALUE", "FOUR_PLUS", "DIVERSIFIED", "PUBLISHABLE", 40),
        ("u_zero", "NO_VALUE", "ONE_ITEM", "UNKNOWN", "DIRECTIONAL", 0),
    ]
    assert context == (
        result.build_id,
        date(2018, 2, 2),
        config.SCHEMA_VERSION,
        config.SEGMENTATION_VERSION,
    )
    assert geography == pytest.approx((-23.55, -46.65, "SP", 2))


def test_order_summary_preaggregates_payments_and_reviews_without_fanout(
    isolated_paths, built_compact
):
    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        order = connection.execute(
            """
            SELECT units, merchandise_gmv_brl, freight_value_brl, paid_value_brl,
                   payment_rows, payment_methods, review_score, review_rows,
                   delivery_delay_days, is_late
            FROM mart_order_summary WHERE order_id = 'o_b'
            """
        ).fetchone()

    assert order == (2, 150, 2, 152, 2, 2, 2.0, 2, 2, True)


def test_as_of_date_excludes_later_orders_and_rebuild_is_reproducible(
    isolated_paths, compact_snapshot
):
    ingest.ingest_all()
    first = build.build_analytics(as_of=date(2018, 1, 31))
    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        january_customers = connection.execute(
            "SELECT customer_unique_id FROM mart_customer_segmentation_asof ORDER BY 1"
        ).fetchall()
    second = build.build_analytics(as_of=date(2018, 1, 31))

    assert january_customers == [("u_a",), ("u_b",)]
    assert second.as_of_date == first.as_of_date
    assert second.build_id != first.build_id


def test_build_rolls_back_context_and_partial_sql_on_failure(
    isolated_paths, built_compact, monkeypatch, tmp_path
):
    previous_build = built_compact[1].build_id
    sql_dir = tmp_path / "broken_sql"
    sql_dir.mkdir()
    (sql_dir / "01_schema.sql").write_text("CREATE TABLE partial_marker AS SELECT 1 AS n;")
    (sql_dir / "02_marts.sql").write_text("THIS IS NOT SQL;")
    (sql_dir / "03_quality_checks.sql").write_text("SELECT 1;")
    monkeypatch.setattr(build, "SQL_DIR", sql_dir)

    with pytest.raises(duckdb.Error):
        build.build_analytics(date(2018, 2, 2))

    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        current_build = connection.execute("SELECT build_id FROM build_context").fetchone()[0]
        marker = connection.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='partial_marker'"
        ).fetchone()[0]
    assert current_build == previous_build
    assert marker == 0


def test_quality_checks_detect_source_defects_and_segmentation_excludes_negative_items(
    isolated_paths, compact_snapshot
):
    ingest.ingest_all()
    with duckdb.connect(str(isolated_paths.database)) as connection:
        connection.execute("UPDATE raw_order_items SET price='-1' WHERE order_id='o_zero'")
    build.build_analytics()

    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        checks = _fetch_map(
            connection,
            "SELECT check_id, status FROM quality_checks ORDER BY check_id",
        )
        customers = connection.execute(
            "SELECT customer_unique_id FROM mart_customer_segmentation_asof ORDER BY 1"
        ).fetchall()
    assert checks["negative_item_values"] == "FAIL"
    assert ("u_zero",) not in customers
    assert all(
        checks[name] == "PASS"
        for name in (
            "orders_pk_unique",
            "items_without_order",
            "items_without_product",
            "items_without_seller",
            "customer_gmv_reconciliation",
        )
    )


def test_coverage_thresholds_and_grouped_fanout_use_business_grain(
    isolated_paths, snapshot_factory
):
    snapshot_factory("publishable")
    ingest.ingest_all()
    build.build_analytics()

    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        category = connection.execute(
            "SELECT orders, units, customers, coverage_status FROM mart_category_performance"
        ).fetchone()
        seller = connection.execute(
            "SELECT orders, units, coverage_status FROM mart_seller_performance"
        ).fetchone()
        delivery = connection.execute(
            "SELECT delivery_status, orders, reviewed_orders, coverage_status "
            "FROM mart_delivery_experience ORDER BY delivery_status"
        ).fetchall()
        affinity = connection.execute(
            "SELECT customers, units, coverage_status FROM mart_customer_category_affinity"
        ).fetchone()
        cross_status = connection.execute(
            "SELECT coverage_status FROM mart_customer_cross_segment"
        ).fetchone()[0]
        high_failures = connection.execute(
            "SELECT COUNT(*) FROM quality_checks WHERE severity='HIGH' AND status='FAIL'"
        ).fetchone()[0]

    assert category == (60, 60, 1, "PUBLISHABLE")
    assert seller == (60, 60, "PUBLISHABLE")
    assert delivery == [
        ("LATE", 30, 30, "PUBLISHABLE"),
        ("ON_TIME", 30, 30, "PUBLISHABLE"),
    ]
    assert affinity == (1, 60, "SUPPRESSED")
    assert cross_status == "SUPPRESSED"
    assert high_failures == 0
