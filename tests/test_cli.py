from datetime import date

import pytest

from ecommerce_clientes import pipeline


def _record_pipeline(monkeypatch):
    calls = []
    monkeypatch.setattr(
        pipeline, "download_all", lambda force=False: calls.append(("download", force))
    )
    monkeypatch.setattr(pipeline, "ingest_all", lambda force=False: calls.append(("ingest", force)))
    monkeypatch.setattr(
        pipeline, "build_analytics", lambda as_of=None: calls.append(("build", as_of))
    )
    monkeypatch.setattr(pipeline, "validate", lambda: calls.append(("validate",)))
    monkeypatch.setattr(pipeline, "export_all", lambda: calls.append(("export",)))
    return calls


@pytest.mark.parametrize(
    ("stage", "expected"),
    [
        ("download", [("download", True)]),
        ("ingest", [("ingest", True)]),
        ("build", [("build", date(2018, 3, 1))]),
        ("validate", [("validate",)]),
        ("export", [("export",)]),
    ],
)
def test_cli_dispatches_single_stage(monkeypatch, stage, expected):
    calls = _record_pipeline(monkeypatch)
    monkeypatch.setattr(
        "sys.argv", ["ecommerce-clientes", stage, "--force", "--as-of", "2018-03-01"]
    )

    pipeline.main()

    assert calls == expected


def test_cli_all_runs_stages_in_dependency_order(monkeypatch):
    calls = _record_pipeline(monkeypatch)
    monkeypatch.setattr(
        "sys.argv", ["ecommerce-clientes", "all", "--force", "--as-of", "2018-02-28"]
    )

    pipeline.main()

    assert calls == [
        ("download", True),
        ("ingest", True),
        ("build", date(2018, 2, 28)),
        ("validate",),
        ("export",),
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ["ecommerce-clientes", "unknown"],
        ["ecommerce-clientes", "build", "--as-of", "not-a-date"],
    ],
)
def test_cli_rejects_invalid_arguments(monkeypatch, arguments):
    calls = _record_pipeline(monkeypatch)
    monkeypatch.setattr("sys.argv", arguments)

    with pytest.raises(SystemExit) as error:
        pipeline.main()
    assert error.value.code == 2
    assert calls == []
