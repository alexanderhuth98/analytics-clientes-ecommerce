from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORS = {
    "navy": "#17324D",
    "teal": "#167D8D",
    "orange": "#D97941",
    "green": "#668F80",
    "red": "#B94A48",
    "ivory": "#F6F2EA",
    "white": "#FFFDF8",
    "muted": "#657482",
}


def _money(value: float) -> str:
    return f"R$ {value / 1_000_000:,.1f} M".replace(",", "X").replace(".", ",").replace("X", ".")


def _number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _chart_html(figure: go.Figure, include_plotlyjs: bool | str) -> str:
    figure.update_layout(
        paper_bgcolor=COLORS["white"],
        plot_bgcolor=COLORS["white"],
        font={"family": "Arial", "color": COLORS["navy"]},
        margin={"l": 46, "r": 24, "t": 58, "b": 42},
        legend_title_text="",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#E7E0D5")
    return figure.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={"displaylogo": False, "responsive": True},
    )


def render_dashboard(tables: dict[str, pd.DataFrame], mobile: bool = False) -> str:
    monthly = tables["executive_monthly"].copy()
    segments = tables["customer_segment_summary"].copy()
    categories = tables["category_performance"].query("coverage_status == 'PUBLISHABLE'").copy()
    delivery = tables["delivery_experience"].query("coverage_status == 'PUBLISHABLE'").copy()

    monthly["month_start"] = pd.to_datetime(monthly["month_start"])
    monthly = monthly.sort_values("month_start")
    total_gmv = float(monthly["merchandise_gmv_brl"].sum())
    delivered_orders = int(monthly["delivered_orders"].sum())
    units = int(monthly["units"].sum())
    customer_count = int(segments.query("segment_dimension == 'VALUE'")["customers"].sum())
    raw_as_of = str(monthly["as_of_date"].max())
    parsed_as_of = pd.to_datetime(raw_as_of, errors="coerce")
    as_of = escape(str(parsed_as_of.date()) if not pd.isna(parsed_as_of) else raw_as_of)

    monthly_fig = px.line(
        monthly,
        x="month_start",
        y="merchandise_gmv_brl",
        markers=True,
        title="GMV mensual de pedidos entregados",
        labels={"month_start": "Mes", "merchandise_gmv_brl": "GMV (R$)"},
        color_discrete_sequence=[COLORS["teal"]],
    )
    value = segments.query("segment_dimension == 'VALUE'").sort_values("merchandise_gmv_brl")
    value_fig = px.bar(
        value,
        x="merchandise_gmv_brl",
        y="segment_label",
        orientation="h",
        title="Concentracion de GMV por segmento de valor",
        labels={"merchandise_gmv_brl": "GMV (R$)", "segment_label": "Segmento"},
        color="segment_label",
        color_discrete_sequence=[COLORS["orange"], COLORS["teal"], COLORS["green"]],
    )
    top_categories = categories.nlargest(12, "merchandise_gmv_brl").sort_values(
        "merchandise_gmv_brl"
    )
    category_fig = px.bar(
        top_categories,
        x="merchandise_gmv_brl",
        y="category_name",
        orientation="h",
        title="Categorias con mayor GMV publicable",
        labels={"merchandise_gmv_brl": "GMV (R$)", "category_name": "Categoria"},
        color_discrete_sequence=[COLORS["teal"]],
    )
    delivery["weighted_review"] = delivery["avg_review_score"] * delivery["reviewed_orders"]
    delivery_summary = delivery.groupby("delivery_status", as_index=False).agg(
        orders=("orders", "sum"),
        reviewed_orders=("reviewed_orders", "sum"),
        weighted_review=("weighted_review", "sum"),
    )
    delivery_summary["avg_review_score"] = (
        delivery_summary["weighted_review"] / delivery_summary["reviewed_orders"]
    )
    delivery_summary = delivery_summary.sort_values("orders", ascending=False)
    delivery_fig = px.bar(
        delivery_summary,
        x="delivery_status",
        y="avg_review_score",
        text_auto=".2f",
        title="Resena promedio segun cumplimiento de entrega",
        labels={"delivery_status": "Entrega", "avg_review_score": "Review promedio"},
        color="delivery_status",
        color_discrete_map={"ON_TIME": COLORS["green"], "LATE": COLORS["red"]},
    )
    value_fig.update_layout(showlegend=False)
    delivery_fig.update_layout(showlegend=False)
    charts = [monthly_fig, value_fig, category_fig, delivery_fig]
    chart_blocks = []
    for index, figure in enumerate(charts):
        chart_blocks.append(_chart_html(figure, index == 0))

    columns = "one" if mobile else "two"
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clientes y performance e-commerce</title>
<style>
:root {{ --navy:{COLORS["navy"]}; --teal:{COLORS["teal"]}; --ivory:{COLORS["ivory"]};
--white:{COLORS["white"]}; --muted:{COLORS["muted"]}; }}
* {{ box-sizing:border-box; }}
html,body {{ width:100%; max-width:100%; overflow-x:hidden; }}
body {{ margin:0; background:var(--ivory); color:var(--navy); font-family:Arial,sans-serif; }}
main {{ width:100%; max-width:1240px; margin:auto; padding:32px 22px 60px; }}
.eyebrow {{ color:var(--teal); font-size:12px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; }}
h1 {{ font-size:clamp(28px,5vw,48px); margin:8px 0 6px; }}
.subtitle {{ color:var(--muted); max-width:780px; line-height:1.5; }}
.cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:26px 0; }}
.card,.panel {{ background:var(--white); border:1px solid #E2DBD0; border-radius:10px; }}
.card {{ padding:18px; }} .card span {{ display:block; color:var(--muted); font-size:13px; }}
.card strong {{ display:block; font-size:25px; margin-top:7px; }}
.grid {{ display:grid; grid-template-columns:{"1fr" if columns == "one" else "repeat(2,minmax(0,1fr))"}; gap:18px; min-width:0; }}
.panel {{ min-height:410px; min-width:0; overflow:hidden; }}
.panel .plotly-graph-div,.panel .plot-container,.panel .svg-container {{ width:100% !important; max-width:100% !important; }}
.note {{ margin-top:22px; padding:18px; border-left:4px solid var(--teal); background:var(--white); line-height:1.5; }}
footer {{ color:var(--muted); font-size:12px; margin-top:28px; }}
@media(max-width:760px) {{ main {{ width:100vw; max-width:100vw; padding:22px 12px 40px; overflow:hidden; }} .subtitle,.cards,.grid {{ width:calc(100vw - 24px); max-width:calc(100vw - 24px); }} .subtitle {{ overflow-wrap:anywhere; }} .cards {{ grid-template-columns:1fr; }} .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><main>
<div class="eyebrow">Olist · corte {as_of}</div>
<h1>Clientes y performance e-commerce</h1>
<p class="subtitle">Segmentacion defendible por facturacion, unidades y amplitud de categorias. Los importes corresponden a articulos de pedidos entregados; el flete se informa por separado.</p>
<section class="cards">
<div class="card"><span>GMV entregado</span><strong>{_money(total_gmv)}</strong></div>
<div class="card"><span>Clientes segmentados</span><strong>{_number(customer_count)}</strong></div>
<div class="card"><span>Pedidos entregados</span><strong>{_number(delivered_orders)}</strong></div>
<div class="card"><span>Unidades</span><strong>{_number(units)}</strong></div>
</section>
<section class="grid">{"".join(f'<div class="panel">{chart}</div>' for chart in chart_blocks)}</section>
<div class="note"><strong>Lectura correcta.</strong> ABC describe concentracion historica de GMV dentro del corte. No mide rentabilidad, fidelidad ni potencial causal. Los grupos con cobertura insuficiente permanecen suprimidos.</div>
<footer>Fuente: Brazilian E-Commerce Public Dataset by Olist, Kaggle. Pipeline reproducible con DuckDB y quality gates.</footer>
</main></body></html>"""
