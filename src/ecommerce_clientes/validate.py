from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from .config import DATABASE_PATH, OUTPUT_DIR, PROJECT_ROOT


@dataclass(frozen=True)
class ValidationResult:
    build_id: str
    as_of_date: str
    high_failures: int
    medium_warnings: int
    checks: int
    report_path: Path


def _report(checks: pd.DataFrame, build_id: str, as_of_date: str) -> str:
    high_failures = checks.query("severity == 'HIGH' and status == 'FAIL'")
    warnings = checks.query("severity == 'MEDIUM' and status == 'FAIL'")
    lines = [
        "# Informe de validacion",
        "",
        f"**Build:** `{build_id}`  ",
        f"**Corte:** `{as_of_date}`  ",
        f"**Controles:** `{len(checks)}`  ",
        f"**Fallas altas:** `{len(high_failures)}`  ",
        f"**Advertencias medias:** `{len(warnings)}`",
        "",
        "## Resultado",
        "",
        (
            "El build supera los controles bloqueantes y puede publicarse."
            if high_failures.empty
            else "El build no es publicable hasta resolver los controles altos."
        ),
        "",
        "## Controles",
        "",
        "| Control | Severidad | Estado | Observado | Umbral |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in checks.itertuples(index=False):
        lines.append(
            f"| `{row.check_id}` | {row.severity} | {row.status} | "
            f"{row.observed_value:,.2f} | {row.threshold:,.2f} |"
        )
    lines.extend(
        [
            "",
            "## Criterio",
            "",
            "Las fallas `HIGH` bloquean la publicacion. Las fallas `MEDIUM` permanecen visibles "
            "como limitaciones y no se corrigen silenciosamente.",
            "",
        ]
    )
    return "\n".join(lines)


def validate(raise_on_failure: bool = True) -> ValidationResult:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError("No existe el warehouse. Ejecute primero ingest y build.")
    with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
        checks = connection.execute(
            "SELECT * FROM quality_checks ORDER BY severity, check_id"
        ).fetchdf()
        context = connection.execute("SELECT build_id, as_of_date FROM build_context").fetchone()
    if checks.empty:
        raise ValueError("El build no contiene controles de calidad.")
    build_id, as_of = context[0], str(context[1])
    high_failures = int(((checks["severity"] == "HIGH") & (checks["status"] == "FAIL")).sum())
    warnings = int(((checks["severity"] == "MEDIUM") & (checks["status"] == "FAIL")).sum())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_dir = PROJECT_ROOT / "reports" / as_of
    report_dir.mkdir(parents=True, exist_ok=True)
    text = _report(checks, build_id, as_of)
    output_report = OUTPUT_DIR / "validation_report.md"
    output_report.write_text(text, encoding="utf-8")
    report_path = report_dir / "validation_report.md"
    report_path.write_text(text, encoding="utf-8")
    result = ValidationResult(build_id, as_of, high_failures, warnings, len(checks), report_path)
    if high_failures and raise_on_failure:
        raise RuntimeError(
            f"El build tiene {high_failures} controles HIGH fallidos. Ver {report_path}"
        )
    return result
