# Registro de limpieza

## Principio

La limpieza privilegia trazabilidad sobre correccion cosmetica. Los valores invalidos no
se reescriben para mejorar indicadores: se tipan cuando es seguro, se clasifican como
desconocidos o se excluyen solo de la metrica afectada con un control visible.

## Ingesta

| Paso | Tratamiento |
|---|---|
| Contrato | Exige los nombres y el orden exactos de columnas para los 9 CSV. |
| Parser | DuckDB `read_csv`, encabezado, todas las columnas como texto, muestra completa y modo estricto. |
| Publicacion | Carga en base staging y reemplaza el warehouse solo al completar. |
| Reconciliacion | Registra 9 tablas y `1.550.922` filas fuente. |

Filas por tabla del snapshot:

| Tabla raw | Filas |
|---|---:|
| `raw_geolocation` | 1.000.163 |
| `raw_order_items` | 112.650 |
| `raw_order_payments` | 103.886 |
| `raw_customers` | 99.441 |
| `raw_orders` | 99.441 |
| `raw_order_reviews` | 99.224 |
| `raw_products` | 32.951 |
| `raw_sellers` | 3.095 |
| `raw_product_category_name_translation` | 71 |

## Normalizacion

| Dominio | Cambio | Justificacion |
|---|---|---|
| Texto | `TRIM` y cadenas vacias a `NULL` | Evita categorias o estados vacios ficticios. |
| Estados de pedido/pago | Minusculas | Unifica comparaciones. |
| Estados geograficos | Mayusculas | Unifica codigos estatales. |
| Numeros y fechas | `TRY_CAST` | Un valor no convertible queda nulo sin inventar un reemplazo. |
| Importes | `DECIMAL(18,2)` | Conserva centavos para GMV, flete y pagos. |
| Categoria | Traduccion inglesa; faltante a `unknown` | Mantiene cobertura faltante visible. |
| Geografia | Mediana lat/lng y moda ciudad/estado por prefijo | Reduce duplicacion del dataset geografico al grano postal. |

## Identidad

No se deduplica `customer_id` contra `customer_unique_id`. Se construye un puente que
conserva la direccion observada para el pedido, mientras `dim_customer` queda a nivel
`customer_unique_id`. Esta separacion evita confundir checkout/direccion con cliente.

## Excepciones preservadas

| Hallazgo | Conteo | Decision |
|---|---:|---|
| Cronologia invalida | 23 pedidos | Excluir de entrega/experiencia; conservar en hechos y control. |
| Diferencia pago vs. GMV + flete mayor a R$ 1 | 256 pedidos | Informar; no imputar pagos o precios. |
| Entregado sin review | 646 pedidos | Mantener review nula. |
| Producto sin categoria | 623 productos | Etiquetar `unknown`. |

Los 623 productos desconocidos generan una categoria agregada visible. No equivalen al
conteo de items, pedidos o clientes afectados.

## Duplicados e integridad

El build de referencia encontro cero fallas en:

- Unicidad de `order_id`.
- Unicidad de `customer_id` en el puente.
- Unicidad de `order_id + order_item_id`.
- Items sin pedido, producto o seller.
- Pedidos sin `customer_unique_id` resuelto.
- Valores de item negativos.
- Duplicacion o incompletitud de segmentacion.
- Reconciliacion de GMV elegible dentro de R$ `0,01`.

Esto valida las reglas definidas, no prueba ausencia de duplicados semanticos no
identificables en una fuente anonimizada.

## Datos no imputados

- Categorias faltantes.
- Reviews faltantes.
- Fechas invalidas o ausentes.
- Diferencias de pago.
- Costos, margen, devoluciones o valor de cliente no presentes en la fuente.
