# Arquitectura

## Vista general

```text
Kaggle API
  -> data/raw/brazilian-ecommerce.zip
  -> data/raw/olist/*.csv
  -> data/warehouse/ecommerce.duckdb
       -> raw_* (texto)
       -> dimensiones y hechos tipados
       -> mart_order_summary
       -> marts analiticos + quality_checks
  -> outputs/ + reports/ + portfolio_data/ + site/
  -> Power BI sobre portfolio_data/
```

`data/`, Parquet, Excel y otros binarios no se versionan. `portfolio_data/` contiene solo
agregados anonimizados. `site/` contiene los HTML generados que puede desplegar Pages.

## Capas

| Capa | Artefactos | Responsabilidad |
|---|---|---|
| Adquisicion | `download.py`, `manifests/raw_sources.jsonl` | Descargar, validar miembros ZIP y registrar SHA-256. |
| Ingesta | `ingest.py`, tablas `raw_*` | Cargar los 9 CSV como texto y validar contrato exacto. |
| Modelo | `sql/01_schema.sql` | Tipar dimensiones/hechos y resolver claves. |
| Marts | `sql/02_marts.sql` | Fijar granos, agregar fanout y calcular segmentos. |
| Calidad | `sql/03_quality_checks.sql`, `validate.py` | Ejecutar gates y bloquear fallas `HIGH`. |
| Entrega | `export.py`, `dashboard.py` | Generar tablas, reportes, Excel, HTML y datos de portfolio. |
| Consumo | `site/`, `powerbi/` | Presentar exclusivamente agregados publicados. |

## Granos principales

| Tabla | Grano |
|---|---|
| `dim_customer` | Un `customer_unique_id`. |
| `bridge_customer_order_address` | Un `customer_id` de pedido/direccion. |
| `dim_product` | Un producto. |
| `dim_seller` | Un vendedor anonimizado. |
| `dim_geography` | Un prefijo postal agregado. |
| `fct_order` | Un pedido. |
| `fct_order_item` | Un item dentro de un pedido. |
| `fct_payment` | Una secuencia de pago dentro de un pedido. |
| `fct_review` | Una review asociada a pedido. |
| `mart_order_summary` | Un pedido con items, pagos y reviews agregados. |
| `mart_customer_segmentation_asof` | Un cliente analitico al corte. |

## Identidad de cliente

`customer_id` no se usa como persona persistente. Es la clave que une un pedido con la
fila de cliente/direccion observada. `customer_unique_id` es la clave anonima estable que
permite agregar pedidos del mismo cliente analitico. En el snapshot existen `99.441`
pedidos y `customer_id`, frente a `96.096` `customer_unique_id` distintos.

El puente conserva la direccion asociada a cada pedido y evita sobrescribirla con una
direccion supuestamente maestra.

## Control de fanout

Tres hechos tienen multiplicidad por pedido:

| Relacion | Pedidos con mas de una fila |
|---|---:|
| Items | 9.803 |
| Pagos | 2.961 |
| Reviews | 547 |

`mart_order_summary` agrega cada tabla por `order_id` en CTE independientes y recien
despues las une a `fct_order`. Esto impide que, por ejemplo, dos items por dos pagos
produzcan cuatro filas y dupliquen GMV.

Los marts de categoria y vendedor vuelven al grano item porque atribuyen GMV a producto o
seller. Al unir `mart_order_summary`, la review del pedido se pondera por item en esos
marts. No debe interpretarse como promedio estrictamente ponderado por pedido.

## Transacciones y recuperacion

- La descarga escribe `.part` y reemplaza el ZIP al terminar.
- La extraccion valida path traversal y usa un directorio staging.
- La ingesta crea una base staging y conserva la anterior si la publicacion falla.
- El build ejecuta esquema, marts y controles dentro de una transaccion.
- La exportacion valida primero y genera archivos en staging, pero copia los destinos de
  manera individual; no se declara atomicidad del conjunto de outputs.

## Linaje

- `raw_sources.jsonl`: URL, fecha de descarga, bytes, SHA-256 y archivos.
- `ingest_state`: `ingest_run_id`, version de esquema, tablas y filas fuente.
- `build_context`: `build_id`, corte, version de esquema y segmentacion.
- Cada CSV publico incluye `build_id` y, cuando aplica, `as_of_date`.
- `export_manifest.json` registra filas y estado de calidad de la exportacion local.

## Frontera publica

No se publican raw, DuckDB, Parquet detallado, texto de reviews ni filas de cliente,
pedido o pago. Power BI y el dashboard consumen marts agregados. Los grupos comparativos
con menos de 30 observaciones quedan `SUPPRESSED` segun la unidad definida por cada mart.
