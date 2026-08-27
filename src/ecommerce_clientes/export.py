import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd

from .config import (
    DATABASE_PATH,
    EXPORT_DIR,
    OUTPUT_DIR,
    PORTFOLIO_DATA_DIR,
    PROJECT_ROOT,
    SITE_DIR,
    ensure_directories,
)
from .dashboard import render_dashboard
from .validate import validate

EXPORT_TABLES = {
    "executive_monthly": "mart_executive_monthly",
    "customer_segment_summary": "mart_customer_segment_summary",
    "customer_cross_segment": "mart_customer_cross_segment",
    "customer_category_affinity": "mart_customer_category_affinity",
    "category_performance": "mart_category_performance",
    "seller_performance": "mart_seller_performance",
    "delivery_experience": "mart_delivery_experience",
    "quality_checks": "quality_checks",
}


@dataclass(frozen=True)
class ExportResult:
    build_id: str
    as_of_date: str
    exported_tables: int
    exported_rows: int
    dashboard_path: str


def _weighted_review(frame: pd.DataFrame) -> float | None:
    reviewed_orders = frame["reviewed_orders"].sum()
    if reviewed_orders <= 0:
        return None
    return float((frame["avg_review_score"] * frame["reviewed_orders"]).sum() / reviewed_orders)


def _executive_report(tables: dict[str, pd.DataFrame], build_id: str, as_of: str) -> str:
    monthly = tables["executive_monthly"]
    segments = tables["customer_segment_summary"]
    delivery = tables["delivery_experience"]
    categories = tables["category_performance"]
    value = segments.query("segment_dimension == 'VALUE'")
    segment_a = value.query("segment_label == 'A_HIGH_VALUE'").iloc[0]
    public_categories = categories.query("coverage_status == 'PUBLISHABLE'").nlargest(
        1, "merchandise_gmv_brl"
    )
    on_time = delivery.query("delivery_status == 'ON_TIME' and coverage_status == 'PUBLISHABLE'")
    late = delivery.query("delivery_status == 'LATE' and coverage_status == 'PUBLISHABLE'")
    on_time_score = _weighted_review(on_time)
    late_score = _weighted_review(late)
    total_gmv = monthly["merchandise_gmv_brl"].sum()
    customers = int(value["customers"].sum())
    category_finding = (
        f"La categoria publicable con mayor GMV es `{public_categories.iloc[0]['category_name']}` "
        f"con `R$ {public_categories.iloc[0]['merchandise_gmv_brl']:,.2f}`."
        if not public_categories.empty
        else "No existe una categoria con cobertura suficiente para publicar un ranking."
    )
    experience_finding = (
        f"La review media fue `{on_time_score:.2f}` en entregas a tiempo y "
        f"`{late_score:.2f}` en entregas tardias."
        if on_time_score is not None and late_score is not None
        else "No existe cobertura suficiente para comparar reviews por cumplimiento de entrega."
    )
    return f"""# Resumen ejecutivo

**Build:** `{build_id}`  
**Corte:** `{as_of}`

## Impacto en 60 segundos

| Resultado | Hallazgo |
|---|---|
| Escala | `{customers:,.0f}` clientes elegibles generaron `R$ {total_gmv:,.2f}` de GMV en articulos entregados. |
| Concentracion | El segmento A reune `{segment_a["customers"]:,.0f}` clientes y `{segment_a["gmv_share"]:.1%}` del GMV. |
| Mix | {category_finding} |
| Experiencia | {experience_finding} |
| Alcance | La segmentacion utiliza facturacion, unidades y categorias; no infiere rentabilidad ni fidelidad. |

## Acciones

1. Priorizar cross-selling sobre clientes A y B con una sola categoria observada.
2. Separar estrategias de alto valor de las de alto volumen: no representan el mismo comportamiento.
3. Revisar vendedores y categorias con suficiente cobertura, alta demora y baja review.
4. Mantener categorias desconocidas como limitacion visible; no imputarlas para mejorar resultados.

## Limitaciones

- Olist es un dataset historico y anonimizado; describe la red observada entre 2016 y 2018.
- GMV excluye flete y no representa beneficio porque no existen costos completos.
- La mayoria de los clientes tiene baja recurrencia; no se publica una segmentacion de fidelidad.
- Las asociaciones entre demora y review son descriptivas, no causales.
"""


def _write_excel(path: Path, tables: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in tables.items():
            safe = frame.copy()
            for column in safe.select_dtypes(include="object"):
                safe[column] = safe[column].map(
                    lambda value: "'" + value
                    if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                    else value
                )
            safe.to_excel(writer, sheet_name=name[:31], index=False)


def _public_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {
        name: (
            frame.loc[frame["coverage_status"].eq("PUBLISHABLE")].copy()
            if "coverage_status" in frame.columns
            else frame.copy()
        )
        for name, frame in tables.items()
    }


def export_all() -> ExportResult:
    ensure_directories()
    validation = validate()
    tables: dict[str, pd.DataFrame] = {}
    with duckdb.connect(str(DATABASE_PATH), read_only=True) as connection:
        for public_name, table_name in EXPORT_TABLES.items():
            tables[public_name] = connection.execute(f"SELECT * FROM {table_name}").fetchdf()

    staging = EXPORT_DIR / f".export-{validation.build_id}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for name, frame in tables.items():
        frame.to_csv(staging / f"{name}.csv", index=False, encoding="utf-8")
        frame.to_parquet(staging / f"{name}.parquet", index=False)

    public_tables = _public_tables(tables)
    desktop_html = render_dashboard(public_tables)
    mobile_html = render_dashboard(public_tables, mobile=True)
    (staging / "dashboard_clientes_ecommerce.html").write_text(desktop_html, encoding="utf-8")
    (staging / "dashboard_mobile.html").write_text(mobile_html, encoding="utf-8")
    _write_excel(staging / "analytics_clientes_ecommerce.xlsx", tables)

    report = _executive_report(tables, validation.build_id, validation.as_of_date)
    (staging / "resumen_ejecutivo.md").write_text(report, encoding="utf-8")
    metadata = {
        **asdict(validation),
        "report_path": str(validation.report_path),
        "exported_at": datetime.now(UTC).isoformat(),
        "rows": {name: len(frame) for name, frame in tables.items()},
    }
    (staging / "export_manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2, default=str), encoding="utf-8"
    )

    for path in staging.iterdir():
        destination = OUTPUT_DIR / path.name
        if destination.exists():
            destination.unlink()
        shutil.copy2(path, destination)

    PORTFOLIO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in public_tables.items():
        frame.to_csv(PORTFOLIO_DATA_DIR / f"{name}.csv", index=False, encoding="utf-8")

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "index.html").write_text(desktop_html, encoding="utf-8")
    (SITE_DIR / "mobile.html").write_text(mobile_html, encoding="utf-8")
    report_dir = PROJECT_ROOT / "reports" / validation.as_of_date
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "resumen_ejecutivo.md").write_text(report, encoding="utf-8")
    shutil.rmtree(staging)

    return ExportResult(
        validation.build_id,
        validation.as_of_date,
        len(tables),
        sum(len(frame) for frame in tables.values()),
        str(OUTPUT_DIR / "dashboard_clientes_ecommerce.html"),
    )
