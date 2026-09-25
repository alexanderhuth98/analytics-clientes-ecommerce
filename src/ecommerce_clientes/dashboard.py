from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORS = {
    "bg": "#0b1111",
    "bg_deep": "#080d0d",
    "surface": "#171d1e",
    "surface_raised": "#1b2223",
    "surface_soft": "#111819",
    "text": "#edf1ef",
    "muted": "#a5aeaa",
    "dim": "#89938f",
    "mint": "#9ef6e5",
    "mint_bright": "#58e4d0",
    "amber": "#f3ce62",
}

SEGMENT_LABELS = {
    "A_HIGH_VALUE": "A · Alto valor",
    "B_MEDIUM_VALUE": "B · Valor medio",
    "C_LOW_VALUE": "C · Bajo valor",
    "NO_VALUE": "Sin valor elegible",
    "ONE_ITEM": "Una unidad",
    "TWO_TO_THREE": "De dos a tres unidades",
    "FOUR_PLUS": "Cuatro unidades o más",
    "SPECIALIST": "Especialista",
    "MIXED": "Mix de categorías",
    "DIVERSIFIED": "Diversificado",
    "UNKNOWN": "Sin categoría conocida",
}

DIMENSION_LABELS = {
    "VALUE": "Valor de compra",
    "UNITS": "Unidades compradas",
    "CATEGORIES": "Amplitud de categorías",
}

DELIVERY_STATUS_LABELS = {
    "ON_TIME": "A tiempo",
    "LATE": "Con demora",
    "UNKNOWN": "Sin estado informado",
}

# The source taxonomy is English and occasionally misspelled. Keeping the translation
# explicit prevents a newly published source code from leaking into the dashboard.
CATEGORY_LABELS = {
    "agro_industry_and_commerce": "Agroindustria y comercio",
    "air_conditioning": "Climatización",
    "art": "Arte",
    "arts_and_craftmanship": "Arte y artesanías",
    "audio": "Audio",
    "auto": "Automotores",
    "baby": "Bebés",
    "bed_bath_table": "Dormitorio, baño y mesa",
    "books_general_interest": "Libros de interés general",
    "books_imported": "Libros importados",
    "books_technical": "Libros técnicos",
    "cds_dvds_musicals": "CD, DVD y musicales",
    "christmas_supplies": "Artículos navideños",
    "cine_photo": "Cine y fotografía",
    "computers": "Computación",
    "computers_accessories": "Accesorios de computación",
    "consoles_games": "Consolas y videojuegos",
    "construction_tools_construction": "Herramientas para construcción",
    "construction_tools_lights": "Iluminación para construcción",
    "construction_tools_safety": "Seguridad para construcción",
    "cool_stuff": "Artículos novedosos",
    "costruction_tools_garden": "Herramientas de jardín",
    "costruction_tools_tools": "Herramientas de construcción",
    "diapers_and_hygiene": "Pañales e higiene",
    "drinks": "Bebidas",
    "dvds_blu_ray": "DVD y Blu-ray",
    "electronics": "Electrónica",
    "fashio_female_clothing": "Indumentaria femenina",
    "fashion_bags_accessories": "Bolsos y accesorios",
    "fashion_childrens_clothes": "Indumentaria infantil",
    "fashion_male_clothing": "Indumentaria masculina",
    "fashion_shoes": "Calzado",
    "fashion_sport": "Indumentaria deportiva",
    "fashion_underwear_beach": "Ropa interior y de playa",
    "fixed_telephony": "Telefonía fija",
    "flowers": "Flores",
    "food": "Alimentos",
    "food_drink": "Alimentos y bebidas",
    "furniture_bedroom": "Muebles de dormitorio",
    "furniture_decor": "Muebles y decoración",
    "furniture_living_room": "Muebles de living",
    "furniture_mattress_and_upholstery": "Colchones y tapicería",
    "garden_tools": "Herramientas de jardinería",
    "health_beauty": "Salud y belleza",
    "home": "Hogar",
    "home_appliances": "Electrodomésticos",
    "home_appliances_2": "Electrodomésticos especiales",
    "home_comfort_2": "Confort para el hogar II",
    "home_confort": "Confort para el hogar",
    "home_construction": "Construcción para el hogar",
    "housewares": "Artículos para el hogar",
    "industry_commerce_and_business": "Industria, comercio y negocios",
    "kitchen_dining_laundry_garden_furniture": (
        "Muebles de cocina, comedor, lavadero y jardín"
    ),
    "la_cuisine": "Cocina",
    "luggage_accessories": "Equipaje y accesorios",
    "market_place": "Mercado en línea",
    "music": "Música",
    "musical_instruments": "Instrumentos musicales",
    "office_furniture": "Muebles de oficina",
    "party_supplies": "Artículos para fiestas",
    "perfumery": "Perfumería",
    "pet_shop": "Mascotas",
    "security_and_services": "Seguridad y servicios",
    "signaling_and_security": "Señalización y seguridad",
    "small_appliances": "Pequeños electrodomésticos",
    "small_appliances_home_oven_and_coffee": (
        "Pequeños electrodomésticos, hornos y café"
    ),
    "sports_leisure": "Deportes y tiempo libre",
    "stationery": "Librería",
    "tablets_printing_image": "Tabletas, impresión e imagen",
    "telephony": "Telefonía",
    "toys": "Juguetes",
    "unknown": "Sin categoría informada",
    "watches_gifts": "Relojes y regalos",
}

PLOTLY_CONFIG = {
    "displaylogo": False,
    "displayModeBar": True,
    "scrollZoom": False,
    "doubleClick": "reset+autosize",
    "responsive": True,
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "toggleSpikelines",
    ],
    "locale": "es-AR",
    "locales": {
        "es-AR": {
            "dictionary": {
                "Autoscale": "Escala automática",
                "Download plot as a png": "Descargar gráfico como PNG",
                "Pan": "Desplazar",
                "Reset axes": "Restablecer ejes",
                "Zoom": "Acercar o alejar",
                "Zoom in": "Acercar",
                "Zoom out": "Alejar",
            },
            "format": {
                "decimal": ",",
                "thousands": ".",
                "grouping": [3],
                "days": [
                    "domingo",
                    "lunes",
                    "martes",
                    "miércoles",
                    "jueves",
                    "viernes",
                    "sábado",
                ],
                "shortDays": ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
                "months": [
                    "enero",
                    "febrero",
                    "marzo",
                    "abril",
                    "mayo",
                    "junio",
                    "julio",
                    "agosto",
                    "septiembre",
                    "octubre",
                    "noviembre",
                    "diciembre",
                ],
                "shortMonths": [
                    "ene",
                    "feb",
                    "mar",
                    "abr",
                    "may",
                    "jun",
                    "jul",
                    "ago",
                    "sep",
                    "oct",
                    "nov",
                    "dic",
                ],
                "date": "%d/%m/%Y",
            },
        }
    },
}

MONTHS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def _money(value: float) -> str:
    return f"R$ {value / 1_000_000:,.1f} M".replace(",", "X").replace(".", ",").replace("X", ".")


def _currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _decimal(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return escape(parsed.strftime("%d/%m/%Y") if not pd.isna(parsed) else str(value))


def _month_label(value: object) -> str:
    parsed = pd.to_datetime(value)
    return f"{MONTHS[parsed.month - 1]} {parsed.year}"


def _translate(values: pd.Series, labels: dict[str, str], label_type: str) -> pd.Series:
    translated = values.map(labels)
    missing = sorted(values[translated.isna()].dropna().astype(str).unique())
    if missing:
        raise ValueError(f"Faltan traducciones de {label_type}: {', '.join(missing)}")
    return translated


def _chart_html(figure: go.Figure, include_plotlyjs: bool | str) -> str:
    figure.update_layout(
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font={"family": "IBM Plex Mono, monospace", "color": COLORS["text"], "size": 12},
        title={"font": {"family": "Space Grotesk, sans-serif", "size": 18}, "x": 0.04},
        margin={"l": 58, "r": 24, "t": 72, "b": 54},
        legend_title_text="",
        separators=",.",
        hoverlabel={
            "bgcolor": COLORS["surface_raised"],
            "bordercolor": COLORS["mint"],
            "font": {"family": "IBM Plex Mono, monospace", "color": COLORS["text"]},
        },
        hovermode="closest",
    )
    axis = {
        "gridcolor": "rgba(158,246,229,.11)",
        "linecolor": "rgba(158,246,229,.25)",
        "tickcolor": "rgba(158,246,229,.25)",
        "zerolinecolor": "rgba(158,246,229,.25)",
        "title_font": {"family": "IBM Plex Mono, monospace", "color": COLORS["muted"]},
        "tickfont": {"color": COLORS["muted"]},
        "automargin": True,
    }
    figure.update_xaxes(**axis)
    figure.update_yaxes(**axis)
    return figure.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config=PLOTLY_CONFIG,
    )


def render_dashboard(tables: dict[str, pd.DataFrame], mobile: bool = False) -> str:
    monthly = tables["executive_monthly"].copy()
    segments = tables["customer_segment_summary"].copy()
    categories = tables["category_performance"].query("coverage_status == 'PUBLISHABLE'").copy()
    delivery = tables["delivery_experience"].query("coverage_status == 'PUBLISHABLE'").copy()

    monthly["month_start"] = pd.to_datetime(monthly["month_start"])
    monthly = monthly.sort_values("month_start")
    monthly["Mes"] = monthly["month_start"].map(_month_label)
    monthly["GMV"] = monthly["merchandise_gmv_brl"].map(_currency)
    total_gmv = float(monthly["merchandise_gmv_brl"].sum())
    delivered_orders = int(monthly["delivered_orders"].sum())
    units = int(monthly["units"].sum())
    customer_count = int(segments.query("segment_dimension == 'VALUE'")["customers"].sum())
    as_of = _date(monthly["as_of_date"].max())

    monthly_fig = px.line(
        monthly,
        x="Mes",
        y="merchandise_gmv_brl",
        custom_data=["GMV"],
        markers=True,
        title="GMV mensual de pedidos entregados",
        labels={"merchandise_gmv_brl": "GMV de artículos (R$)"},
        color_discrete_sequence=[COLORS["mint_bright"]],
    )
    monthly_fig.update_traces(
        hovertemplate="<b>%{x}</b><br>GMV de artículos: %{customdata[0]}<extra></extra>"
    )
    monthly_fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")

    value = segments.query("segment_dimension == 'VALUE'").sort_values("merchandise_gmv_brl")
    value["Segmento"] = _translate(value["segment_label"], SEGMENT_LABELS, "segmentos")
    value["GMV"] = value["merchandise_gmv_brl"].map(_currency)
    value["Clientes"] = value["customers"].map(_number)
    value_fig = px.bar(
        value,
        x="merchandise_gmv_brl",
        y="Segmento",
        custom_data=["GMV", "Clientes"],
        orientation="h",
        title="Concentración de GMV por segmento de valor",
        labels={"merchandise_gmv_brl": "GMV de artículos (R$)"},
        color="Segmento",
        color_discrete_map={
            SEGMENT_LABELS["A_HIGH_VALUE"]: COLORS["mint_bright"],
            SEGMENT_LABELS["B_MEDIUM_VALUE"]: COLORS["amber"],
            SEGMENT_LABELS["C_LOW_VALUE"]: COLORS["dim"],
            SEGMENT_LABELS["NO_VALUE"]: COLORS["muted"],
        },
    )
    value_fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>GMV de artículos: %{customdata[0]}"
            "<br>Clientes: %{customdata[1]}<extra></extra>"
        )
    )
    value_fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")

    categories["Categoría"] = _translate(
        categories["category_name"], CATEGORY_LABELS, "categorías"
    )
    categories["GMV"] = categories["merchandise_gmv_brl"].map(_currency)
    categories["Pedidos"] = categories["orders"].map(_number)
    top_categories = categories.nlargest(12, "merchandise_gmv_brl").sort_values(
        "merchandise_gmv_brl"
    )
    category_fig = px.bar(
        top_categories,
        x="merchandise_gmv_brl",
        y="Categoría",
        custom_data=["GMV", "Pedidos"],
        orientation="h",
        title="Categorías con mayor GMV publicable",
        labels={"merchandise_gmv_brl": "GMV de artículos (R$)"},
        color_discrete_sequence=[COLORS["mint"]],
    )
    category_fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>GMV de artículos: %{customdata[0]}"
            "<br>Pedidos: %{customdata[1]}<extra></extra>"
        )
    )
    category_fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")

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
    delivery_summary["Entrega"] = _translate(
        delivery_summary["delivery_status"], DELIVERY_STATUS_LABELS, "estados de entrega"
    )
    delivery_summary["Calificación"] = delivery_summary["avg_review_score"].map(_decimal)
    delivery_summary["Pedidos"] = delivery_summary["orders"].map(_number)
    delivery_fig = px.bar(
        delivery_summary,
        x="Entrega",
        y="avg_review_score",
        custom_data=["Calificación", "Pedidos"],
        text="Calificación",
        title="Calificación promedio según cumplimiento de entrega",
        labels={"avg_review_score": "Calificación promedio"},
        color="Entrega",
        color_discrete_map={
            DELIVERY_STATUS_LABELS["ON_TIME"]: COLORS["mint_bright"],
            DELIVERY_STATUS_LABELS["LATE"]: COLORS["amber"],
            DELIVERY_STATUS_LABELS["UNKNOWN"]: COLORS["dim"],
        },
    )
    delivery_fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>Calificación promedio: %{customdata[0]}"
            "<br>Pedidos: %{customdata[1]}<extra></extra>"
        )
    )
    delivery_fig.update_yaxes(range=[0, 5], dtick=1)

    value_fig.update_layout(showlegend=False)
    delivery_fig.update_layout(showlegend=False)
    charts = [monthly_fig, value_fig, category_fig, delivery_fig]
    chart_blocks = [_chart_html(figure, index == 0) for index, figure in enumerate(charts)]
    panel_blocks = "".join(
        (
            '<article class="panel">'
            f'<div class="chart">{chart}</div>'
            '<div class="panel-actions">'
            '<button type="button" class="reset-view" aria-label="Restablecer vista del gráfico">'
            "Restablecer vista"
            "</button></div></article>"
        )
        for chart in chart_blocks
    )

    columns = "1fr" if mobile else "repeat(2,minmax(0,1fr))"
    return f"""<!doctype html>
<html lang="es-AR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Clientes y desempeño e-commerce</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {{ --bg:#0b1111; --bg-deep:#080d0d; --surface:#171d1e; --surface-raised:#1b2223;
--surface-soft:#111819; --text:#edf1ef; --muted:#a5aeaa; --dim:#89938f; --mint:#9ef6e5;
--mint-bright:#58e4d0; --amber:#f3ce62; --border:rgba(158,246,229,.11);
--border-strong:rgba(158,246,229,.25); }}
* {{ box-sizing:border-box; }}
html,body {{ width:100%; max-width:100%; overflow-x:hidden; }}
body {{ margin:0; color:var(--text); font-family:'IBM Plex Mono',monospace; background-color:var(--bg);
background-image:linear-gradient(rgba(158,246,229,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(158,246,229,.025) 1px,transparent 1px),radial-gradient(circle at 78% -20%,rgba(88,228,208,.10),transparent 38%);
background-size:32px 32px,32px 32px,100% 100%; }}
a {{ color:var(--mint); text-underline-offset:4px; }}
a:hover {{ color:var(--text); }}
a:focus-visible,button:focus-visible {{ outline:2px solid var(--mint); outline-offset:3px; }}
main {{ width:100%; max-width:1280px; margin:auto; padding:40px 24px 64px; }}
header {{ padding:26px 0 28px; border-top:1px solid var(--border-strong); border-bottom:1px solid var(--border); }}
.eyebrow {{ color:var(--mint-bright); font-size:12px; font-weight:600; letter-spacing:1.6px; text-transform:uppercase; }}
h1 {{ max-width:900px; margin:12px 0 12px; font-family:'Space Grotesk',sans-serif; font-size:clamp(34px,6vw,68px); line-height:.98; letter-spacing:-.045em; }}
.subtitle {{ max-width:850px; margin:0; color:var(--muted); font-size:clamp(14px,1.6vw,17px); line-height:1.65; }}
.meta {{ display:flex; flex-wrap:wrap; gap:10px 24px; margin-top:22px; color:var(--dim); font-size:12px; }}
.meta span::before {{ content:'// '; color:var(--mint-bright); }}
.cards {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:24px 0; }}
.card,.panel,.note {{ background:linear-gradient(145deg,var(--surface-raised),var(--surface)); border:1px solid var(--border); border-radius:2px; }}
.card {{ min-height:124px; padding:18px; }}
.card span {{ display:block; color:var(--muted); font-size:12px; line-height:1.4; }}
.card strong {{ display:block; margin-top:15px; color:var(--mint); font-family:'Space Grotesk',sans-serif; font-size:clamp(24px,3vw,34px); letter-spacing:-.035em; }}
.grid {{ display:grid; grid-template-columns:{columns}; gap:16px; min-width:0; }}
.panel {{ min-height:440px; min-width:0; overflow:hidden; }}
.chart {{ min-width:0; }}
.panel .plotly-graph-div,.panel .plot-container,.panel .svg-container {{ width:100% !important; max-width:100% !important; }}
.panel-actions {{ display:flex; justify-content:flex-end; padding:0 16px 14px; }}
.reset-view {{ min-height:42px; padding:9px 13px; color:var(--mint); font:600 11px 'IBM Plex Mono',monospace; letter-spacing:.04em; text-transform:uppercase; background:var(--surface-soft); border:1px solid var(--border-strong); border-radius:2px; cursor:pointer; }}
.reset-view:hover {{ color:var(--bg-deep); background:var(--mint); }}
.note {{ margin-top:18px; padding:20px; color:var(--muted); line-height:1.65; }}
.note strong {{ color:var(--amber); font-family:'Space Grotesk',sans-serif; }}
footer {{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:10px 24px; margin-top:24px; padding-top:18px; color:var(--dim); font-size:11px; line-height:1.6; border-top:1px solid var(--border); }}
.modebar {{ opacity:1 !important; }}
.modebar-btn path {{ fill:var(--muted) !important; }}
.modebar-btn:hover path {{ fill:var(--mint) !important; }}
@media(max-width:820px) {{ .cards {{ grid-template-columns:repeat(2,1fr); }} .grid {{ grid-template-columns:1fr; }} }}
@media(max-width:520px) {{ main {{ width:100vw; max-width:100vw; padding:24px 12px 40px; }} header {{ padding-top:18px; }} .cards {{ grid-template-columns:1fr; }} .card {{ min-height:104px; }} .grid {{ width:calc(100vw - 24px); max-width:calc(100vw - 24px); }} .panel {{ min-height:420px; }} .subtitle {{ overflow-wrap:anywhere; }} .modebar {{ transform:scale(.9); transform-origin:top right; }} }}
@media(prefers-reduced-motion:reduce) {{ * {{ scroll-behavior:auto !important; }} }}
</style>
</head>
<body><main>
<header>
<div class="eyebrow">Caso de analítica · Olist</div>
<h1>Clientes y desempeño e-commerce</h1>
<p class="subtitle">Segmentación de clientes por facturación, unidades y amplitud de categorías, con foco en concentración de valor y experiencia de entrega. El GMV considera únicamente artículos de pedidos entregados: excluye el flete, que se conserva como métrica separada en los datos exportados.</p>
<div class="meta"><span>Corte: {as_of}</span><span>Fuente: conjunto público de comercio electrónico de Olist, Kaggle</span><a href="https://alexanderhuth98.github.io/#proyectos">Volver a proyectos</a></div>
</header>
<section class="cards" aria-label="Indicadores principales">
<div class="card"><span>GMV de artículos entregados</span><strong>{_money(total_gmv)}</strong></div>
<div class="card"><span>Clientes segmentados</span><strong>{_number(customer_count)}</strong></div>
<div class="card"><span>Pedidos entregados</span><strong>{_number(delivered_orders)}</strong></div>
<div class="card"><span>Unidades entregadas</span><strong>{_number(units)}</strong></div>
</section>
<section class="grid" aria-label="Visualizaciones analíticas">{panel_blocks}</section>
<aside class="note"><strong>Cómo leerlo.</strong> ABC describe la concentración histórica del GMV dentro del corte. No mide rentabilidad, fidelidad ni potencial causal. Los grupos con cobertura insuficiente se excluyen por completo de la publicación.</aside>
<footer><span>Fuente: conjunto público de comercio electrónico de Olist, Kaggle.</span><span>Proceso reproducible con DuckDB y controles de calidad.</span></footer>
</main>
<script>
document.querySelectorAll('.reset-view').forEach(function (button) {{
  button.addEventListener('click', function () {{
    var graph = button.closest('.panel').querySelector('.plotly-graph-div');
    if (!graph || !window.Plotly) return;
    Plotly.relayout(graph, {{'xaxis.autorange': true, 'yaxis.autorange': true}}).then(function () {{
      Plotly.Plots.resize(graph);
    }});
  }});
}});
</script>
</body></html>"""
