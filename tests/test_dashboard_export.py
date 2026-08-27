import json

import duckdb
import openpyxl
import pandas as pd

from ecommerce_clientes import build, config, dashboard, export, ingest


def _dashboard_tables() -> dict[str, pd.DataFrame]:
    return {
        "executive_monthly": pd.DataFrame(
            [
                {
                    "month_start": "2018-01-01",
                    "as_of_date": "2018-02-01<script>",
                    "merchandise_gmv_brl": 1_250_000,
                    "delivered_orders": 12,
                    "units": 18,
                },
                {
                    "month_start": "2018-02-01",
                    "as_of_date": "2018-02-01<script>",
                    "merchandise_gmv_brl": 750_000,
                    "delivered_orders": 8,
                    "units": 10,
                },
            ]
        ),
        "customer_segment_summary": pd.DataFrame(
            [
                {
                    "segment_dimension": "VALUE",
                    "segment_label": "A_HIGH_VALUE",
                    "customers": 3,
                    "merchandise_gmv_brl": 1_600_000,
                    "gmv_share": 0.8,
                },
                {
                    "segment_dimension": "VALUE",
                    "segment_label": "B_MEDIUM_VALUE",
                    "customers": 7,
                    "merchandise_gmv_brl": 400_000,
                    "gmv_share": 0.2,
                },
            ]
        ),
        "category_performance": pd.DataFrame(
            [
                {
                    "category_name": "home",
                    "merchandise_gmv_brl": 1_500_000,
                    "coverage_status": "PUBLISHABLE",
                },
                {
                    "category_name": "secret-small-cell",
                    "merchandise_gmv_brl": 500_000,
                    "coverage_status": "SUPPRESSED",
                },
            ]
        ),
        "delivery_experience": pd.DataFrame(
            [
                {
                    "delivery_status": "ON_TIME",
                    "orders": 10,
                    "avg_review_score": 4.5,
                    "reviewed_orders": 10,
                    "coverage_status": "PUBLISHABLE",
                },
                {
                    "delivery_status": "LATE",
                    "orders": 5,
                    "avg_review_score": 2.0,
                    "reviewed_orders": 5,
                    "coverage_status": "PUBLISHABLE",
                },
            ]
        ),
    }


def test_display_helpers_use_brazilian_formatting():
    assert dashboard._money(1_250_000) == "R$ 1,2 M"
    assert dashboard._number(12345) == "12.345"


def test_render_dashboard_filters_suppressed_data_and_supports_mobile():
    tables = _dashboard_tables()
    desktop = dashboard.render_dashboard(tables)
    mobile = dashboard.render_dashboard(tables, mobile=True)

    assert desktop.startswith("<!doctype html>")
    assert "R$ 2,0 M" in desktop
    assert "Clientes segmentados</span><strong>10" in desktop
    assert "2018-02-01&lt;script&gt;" in desktop
    assert "secret-small-cell" not in desktop
    assert desktop.count('class="plotly-graph-div"') == 4
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in desktop
    assert "grid-template-columns:1fr" in mobile


def test_chart_html_applies_shared_layout_without_display_logo():
    figure = dashboard.px.line(pd.DataFrame({"x": [1, 2], "y": [2, 3]}), x="x", y="y")
    html = dashboard._chart_html(figure, False)
    assert "displaylogo" in html
    assert config.SEGMENTATION_VERSION not in html


def test_executive_report_calculates_weighted_delivery_scores():
    tables = _dashboard_tables()
    report = export._executive_report(tables, "build-x", "2018-02-01")

    assert "`10` clientes elegibles" in report
    assert "`80.0%` del GMV" in report
    assert "`home` con `R$ 1,500,000.00`" in report
    assert "`4.50` en entregas a tiempo y `2.00`" in report


def test_write_excel_escapes_formula_injection_and_truncates_sheet_names(tmp_path):
    path = tmp_path / "safe.xlsx"
    long_name = "a" * 40
    frame = pd.DataFrame(
        {"text": ["=SUM(1,1)", "+cmd", "-danger", "@link", "normal"], "number": [1, 2, 3, 4, 5]}
    )

    export._write_excel(path, {long_name: frame})

    workbook = openpyxl.load_workbook(path, data_only=False)
    sheet = workbook["a" * 31]
    assert [sheet.cell(row=row, column=1).value for row in range(2, 7)] == [
        "'=SUM(1,1)",
        "'+cmd",
        "'-danger",
        "'@link",
        "normal",
    ]
    assert sheet["B2"].value == 1


def test_public_tables_remove_entire_non_publishable_rows():
    tables = {
        "controlled": pd.DataFrame(
            [
                {"seller_id": "safe", "metric": 30, "coverage_status": "PUBLISHABLE"},
                {"seller_id": "small", "metric": 1, "coverage_status": "SUPPRESSED"},
                {"seller_id": "other", "metric": 5, "coverage_status": "DIRECTIONAL"},
            ]
        ),
        "uncontrolled": pd.DataFrame([{"metric": 10}]),
    }

    public = export._public_tables(tables)

    assert public["controlled"].to_dict("records") == [
        {"seller_id": "safe", "metric": 30, "coverage_status": "PUBLISHABLE"}
    ]
    assert public["uncontrolled"].equals(tables["uncontrolled"])
    assert public["controlled"] is not tables["controlled"]
    assert public["uncontrolled"] is not tables["uncontrolled"]


def test_export_all_publishes_real_tables_dashboard_manifest_and_portfolio(
    isolated_paths, snapshot_factory
):
    snapshot_factory("publishable")
    ingest.ingest_all()
    built = build.build_analytics()
    staging = isolated_paths.exports / f".export-{built.build_id}"
    staging.mkdir(parents=True)
    (staging / "stale.txt").write_text("stale", encoding="utf-8")
    isolated_paths.outputs.mkdir(parents=True, exist_ok=True)
    (isolated_paths.outputs / "dashboard_clientes_ecommerce.html").write_text(
        "old", encoding="utf-8"
    )

    result = export.export_all()

    assert result.build_id == built.build_id
    assert result.as_of_date == "2018-01-01"
    assert result.exported_tables == len(export.EXPORT_TABLES) == 8
    assert result.exported_rows > 0
    assert result.dashboard_path == str(
        isolated_paths.outputs / "dashboard_clientes_ecommerce.html"
    )
    assert not staging.exists()
    assert "Clientes y performance" in (
        isolated_paths.outputs / "dashboard_clientes_ecommerce.html"
    ).read_text(encoding="utf-8")
    assert (isolated_paths.outputs / "analytics_clientes_ecommerce.xlsx").is_file()
    assert (isolated_paths.outputs / "quality_checks.parquet").is_file()
    assert (isolated_paths.site / "index.html").is_file()
    assert (isolated_paths.site / "mobile.html").is_file()
    assert len(list(isolated_paths.portfolio.glob("*.csv"))) == 8
    assert (isolated_paths.root / "reports/2018-01-01/resumen_ejecutivo.md").is_file()

    manifest = json.loads(
        (isolated_paths.outputs / "export_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["build_id"] == built.build_id
    assert set(manifest["rows"]) == set(export.EXPORT_TABLES)
    exported = pd.read_csv(isolated_paths.outputs / "executive_monthly.csv")
    internal_cross = pd.read_csv(isolated_paths.outputs / "customer_cross_segment.csv")
    public_cross = pd.read_csv(isolated_paths.portfolio / "customer_cross_segment.csv")
    with duckdb.connect(str(isolated_paths.database), read_only=True) as connection:
        warehouse_rows = connection.execute(
            "SELECT COUNT(*) FROM mart_executive_monthly"
        ).fetchone()[0]
    assert len(exported) == warehouse_rows
    assert "SUPPRESSED" in set(internal_cross["coverage_status"])
    assert set(public_cross["coverage_status"]) <= {"PUBLISHABLE"}
    public_categories = pd.read_csv(isolated_paths.portfolio / "category_performance.csv")
    assert set(public_categories["coverage_status"]) == {"PUBLISHABLE"}

    for path in isolated_paths.portfolio.glob("*.csv"):
        public_frame = pd.read_csv(path)
        if "coverage_status" in public_frame:
            assert set(public_frame["coverage_status"]) <= {"PUBLISHABLE"}
        assert "SUPPRESSED" not in path.read_text(encoding="utf-8")


def test_export_handles_valid_small_build_without_publishable_groups(isolated_paths, built_compact):
    result = export.export_all()
    assert result.exported_tables == 8
