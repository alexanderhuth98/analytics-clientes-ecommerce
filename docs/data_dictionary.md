# Diccionario de datos

## Convenciones

- Sufijo `_id`: identificador anonimo o tecnico.
- Sufijo `_at`: timestamp.
- Sufijo `_brl`: importe en reales brasilenos.
- `as_of_date`: fecha maxima incluida por el build.
- `build_id`: UUID que identifica una ejecucion analitica.
- `coverage_status`: el modelo interno puede contener `PUBLISHABLE`, `SUPPRESSED` o
  `DIRECTIONAL`; los CSV publicos solo contienen `PUBLISHABLE`.

## Fuentes

| Archivo | Grano | Claves relevantes |
|---|---|---|
| `olist_customers_dataset.csv` | Referencia cliente/direccion por pedido | `customer_id`, `customer_unique_id` |
| `olist_geolocation_dataset.csv` | Punto geografico por prefijo postal | `geolocation_zip_code_prefix` |
| `olist_orders_dataset.csv` | Pedido | `order_id`, `customer_id` |
| `olist_order_items_dataset.csv` | Item de pedido | `order_id`, `order_item_id` |
| `olist_order_payments_dataset.csv` | Secuencia de pago | `order_id`, `payment_sequential` |
| `olist_order_reviews_dataset.csv` | Review asociada a pedido | `review_id`, `order_id` |
| `olist_products_dataset.csv` | Producto | `product_id` |
| `olist_sellers_dataset.csv` | Vendedor | `seller_id` |
| `product_category_name_translation.csv` | Traduccion de categoria | `product_category_name` |

## Modelo interno

| Tabla | Grano | Descripcion |
|---|---|---|
| `dim_customer` | `customer_unique_id` | Cantidad de direcciones/identidades de pedido observadas. |
| `bridge_customer_order_address` | `customer_id` | Resuelve identidad analitica y direccion del pedido. |
| `dim_geography` | `zip_code_prefix` | Mediana de lat/lng, moda de ciudad/estado y puntos fuente. |
| `dim_product` | `product_id` | Categoria PT/EN, fotos, peso y dimensiones. |
| `dim_seller` | `seller_id` | Prefijo postal, ciudad y estado del seller. |
| `fct_order` | `order_id` | Cliente, estado, cronologia y direccion. |
| `fct_order_item` | `order_id + order_item_id` | Producto, seller, precio, flete y limite de envio. |
| `fct_payment` | Secuencia de pago | Tipo, cuotas y valor pagado. |
| `fct_review` | Review | Score, texto y fechas; el texto no se publica. |
| `mart_order_summary` | `order_id` | Agregados de items, pagos, reviews y entrega. |
| `mart_customer_segmentation_asof` | `customer_unique_id` | Features y tres segmentos al corte. |

## CSV publicos

Los archivos de `portfolio_data/` conservan el esquema de cada mart, pero excluyen por
fila completa cualquier registro cuyo `coverage_status` no sea exactamente `PUBLISHABLE`.
Los registros excluidos, sus identificadores y sus metricas solo permanecen en los
artefactos locales ignorados de `outputs/`.

### `executive_monthly.csv`

Grano: un mes de compra por build.

| Campo | Definicion |
|---|---|
| `month_start` | Primer dia del mes de compra. |
| `orders` | Pedidos comprados en el mes, cualquier estado. |
| `customers` | `customer_unique_id` distintos del mes. |
| `delivered_orders` | Pedidos con estado `delivered`. |
| `failed_orders` | Pedidos `canceled` o `unavailable`. |
| `merchandise_gmv_brl` | Precio de items entregados, sin flete. |
| `freight_value_brl` | Flete de items entregados. |
| `units` | Filas de item de pedidos entregados. |
| `avg_order_value_brl` | GMV medio por pedido entregado. |
| `avg_review_score` | Review media de pedidos entregados con review. |
| `late_delivery_rate` | Proporcion tardia entre entregas con estado de demora conocido. |

### `customer_segment_summary.csv`

Grano: dimension y etiqueta de segmento.

| Campo | Definicion |
|---|---|
| `segmentation_version` | Version de reglas. |
| `segment_dimension` | `VALUE`, `UNITS` o `CATEGORIES`. |
| `segment_label` | Etiqueta dentro de la dimension. |
| `customers` | Clientes analiticos del grupo. |
| `merchandise_gmv_brl` | GMV total del grupo. |
| `units` | Items entregados del grupo. |
| `avg_delivered_orders` | Pedidos entregados medios por cliente. |
| `avg_distinct_categories` | Categorias conocidas medias por cliente. |
| `gmv_share` | Share dentro de la misma dimension. |

No sumar `customers` entre dimensiones: cada cliente aparece una vez en cada una y se
triplicaria la poblacion.

### `customer_cross_segment.csv`

Grano: combinacion de segmento de valor, unidades y categorias.

| Campo | Definicion |
|---|---|
| `value_segment` | A, B o C segun GMV. |
| `unit_segment` | `ONE_ITEM`, `TWO_TO_THREE` o `FOUR_PLUS`. |
| `category_segment` | `UNKNOWN`, `SPECIALIST`, `MIXED` o `DIVERSIFIED`. |
| `customers` | Clientes en la combinacion. |
| `merchandise_gmv_brl` | GMV de la combinacion. |
| `units` | Items de la combinacion. |
| `avg_distinct_categories` | Amplitud media. |
| `coverage_status` | Publicable si hay al menos 30 clientes. |

### `customer_category_affinity.csv`

Grano: segmento de valor y categoria.

| Campo | Definicion |
|---|---|
| `value_segment` | Segmento ABC del cliente. |
| `category_name` | Categoria inglesa o `unknown`. |
| `customers` | Clientes distintos que compraron la categoria. |
| `units` | Items del cruce. |
| `merchandise_gmv_brl` | GMV del cruce. |
| `coverage_status` | Publicable con al menos 30 clientes. |

### `category_performance.csv`

Grano: categoria.

| Campo | Definicion |
|---|---|
| `units` | Items entregados. |
| `orders` | Pedidos distintos. |
| `customers` | Clientes distintos. |
| `merchandise_gmv_brl` | GMV de items. |
| `avg_item_value_brl` | Precio medio por item. |
| `avg_review_score` | Review del pedido ponderada por item. |
| `coverage_status` | Publicable con al menos 30 pedidos. |

### `seller_performance.csv`

Grano: vendedor anonimizado.

| Campo | Definicion |
|---|---|
| `seller_id` | Identificador anonimo de seller. |
| `seller_state` | Estado normalizado en mayusculas. |
| `orders` | Pedidos distintos del seller. |
| `units` | Items del seller. |
| `merchandise_gmv_brl` | GMV atribuido al seller. |
| `avg_review_score` | Review de pedido ponderada por item. |
| `late_delivery_rate` | Proporcion tardia sobre items con demora conocida. |
| `coverage_status` | Publicable con al menos 30 pedidos. |

### `delivery_experience.csv`

Grano: mes y estado de entrega.

| Campo | Definicion |
|---|---|
| `delivery_status` | `ON_TIME`, `LATE` o `UNKNOWN`. |
| `orders` | Pedidos entregados del grupo. |
| `avg_review_score` | Review media observada. |
| `avg_delivery_delay_days` | Dias reales menos fecha estimada. Negativo es anticipado. |
| `reviewed_orders` | Pedidos con review. |
| `coverage_status` | Publicable con al menos 30 pedidos. |

### `quality_checks.csv`

Grano: control de calidad por build.

| Campo | Definicion |
|---|---|
| `check_id` | Nombre estable del control. |
| `severity` | `HIGH` bloqueante o `MEDIUM` informativo. |
| `status` | `PASS` si observado es menor o igual al threshold; `FAIL` si no. |
| `observed_value` | Conteo o diferencia observada. |
| `threshold` | Maximo permitido. |
| `details` | Tratamiento o regla controlada. |
