from datetime import date

import duckdb
import pandas as pd
import pytest

from ecommerce_clientes import validate


def test_report_renders_publishability_counts_and_check_rows():
    checks = pd.DataFrame(
        [
            {
                "check_id": "blocking",
                "severity": "HIGH",
                "status": "FAIL",
                "observed_value": 2,
                "threshold": 0,
            },
            {
                "check_id": "warning",
                "severity": "MEDIUM",
                "status": "FAIL",
                "observed_value": 1.5,
                "threshold": 1,
            },
        ]
    )

    report = validate._report(checks, "build-1", "2018-01-01")

    assert "**Fallas altas:** `1`" in report
    assert "**Advertencias medias:** `1`" in report
    assert "no es publicable" in report
    assert "| `warning` | MEDIUM | FAIL | 1.50 | 1.00 |" in report


def test_validate_writes_both_reports_and_returns_real_quality_results(
    isolated_paths, built_compact
):
    result = validate.validate()

    assert result.build_id == built_compact[1].build_id
    assert result.as_of_date == "2018-02-02"
    assert result.high_failures == 0
    assert result.medium_warnings == 1
    assert result.checks == 15
    assert result.report_path == isolated_paths.root / "reports/2018-02-02/validation_report.md"
    output_text = (isolated_paths.outputs / "validation_report.md").read_text(encoding="utf-8")
    assert result.report_path.read_text(encoding="utf-8") == output_text
    assert "supera los controles bloqueantes" in output_text


def test_validate_raises_for_high_failure_but_report_remains_available(
    isolated_paths, built_compact
):
    with duckdb.connect(str(isolated_paths.database)) as connection:
        connection.execute(
            "UPDATE quality_checks SET status='FAIL', observed_value=1 "
            "WHERE severity='HIGH' AND check_id='orders_pk_unique'"
        )

    allowed = validate.validate(raise_on_failure=False)
    assert allowed.high_failures == 1
    with pytest.raises(RuntimeError, match="1 controles HIGH") as error:
        validate.validate()
    assert str(allowed.report_path) in str(error.value)
    assert allowed.report_path.exists()


def test_validate_requires_warehouse(isolated_paths):
    with pytest.raises(FileNotFoundError, match="ingest y build"):
        validate.validate()


def test_validate_rejects_empty_quality_table(isolated_paths):
    isolated_paths.warehouse.mkdir(parents=True)
    with duckdb.connect(str(isolated_paths.database)) as connection:
        connection.execute(
            "CREATE TABLE quality_checks(check_id VARCHAR, severity VARCHAR, status VARCHAR, "
            "observed_value DOUBLE, threshold DOUBLE)"
        )
        connection.execute("CREATE TABLE build_context(build_id VARCHAR, as_of_date DATE)")
        connection.execute("INSERT INTO build_context VALUES ('empty', ?)", [date(2018, 1, 1)])

    with pytest.raises(ValueError, match="no contiene controles"):
        validate.validate()
