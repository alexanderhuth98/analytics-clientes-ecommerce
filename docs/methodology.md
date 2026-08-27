# Metodologia

## Corte y poblacion

El build de referencia usa `as_of_date = 2018-10-17`. La poblacion de segmentacion exige:

- Pedido con estado `delivered`.
- Compra en fecha igual o anterior al corte.
- `customer_unique_id` no nulo.
- Item con `item_value_brl >= 0`.

El resultado contiene `93.358` clientes elegibles. No todos los `96.096` clientes
anonimos de la fuente cumplen esas condiciones.

## Identidad

- `customer_id`: identificador asociado a un pedido y su direccion observada. Es la clave
  de union entre pedidos y la tabla de clientes fuente.
- `customer_unique_id`: identificador anonimo usado para reconocer al mismo cliente entre
  pedidos. Es el grano de segmentacion.

Usar `customer_id` para recurrencia produciria `99.441` identidades, una por pedido en
este snapshot, y ocultaria las compras repetidas observadas en `customer_unique_id`.

## GMV

```text
merchandise_gmv_brl = SUM(order_items.price)
```

Solo se suma mercaderia de pedidos entregados. El flete se conserva por separado. El pago
no reemplaza al GMV porque puede incorporar flete, vouchers, secuencias o ajustes. No hay
costos completos, por lo que GMV no representa margen o beneficio.

## Segmentacion ABC

La version es `CUSTOMER_VALUE_VOLUME_BREADTH_V1`.

1. Se calcula GMV por `customer_unique_id`.
2. Clientes con el mismo GMV forman un bucket para no dividir empates.
3. Los buckets se ordenan de mayor a menor GMV.
4. Se calcula la participacion acumulada anterior a cada bucket.
5. Se asigna A si es `< 0,80`, B si es `< 0,95` y C en otro caso.

| Segmento | Clientes | GMV (R$) | Share GMV |
|---|---:|---:|---:|
| A alto valor | 42.747 | 10.650.288,76 | 80,55% |
| B valor medio | 27.659 | 1.910.292,59 | 14,45% |
| C bajo valor | 22.952 | 660.916,76 | 5,00% |

Los limites se aplican al acumulado anterior, no al percentil de clientes. Por eso los
empates pueden llevar el share de A o B por encima del corte nominal. ABC es descriptivo
del periodo y no asigna causalidad ni valor futuro.

## Segmentacion por unidades

| Regla | Etiqueta | Clientes |
|---|---|---:|
| `units = 1` | `ONE_ITEM` | 81.748 |
| `units between 2 and 3` | `TWO_TO_THREE` | 10.443 |
| `units >= 4` | `FOUR_PLUS` | 1.167 |

`units` cuenta filas de item entregadas, no cantidad fisica dentro de un SKU si la fuente
la representara de otra manera.

## Segmentacion por categorias

Solo cuentan categorias distintas diferentes de `unknown`.

| Regla | Etiqueta | Clientes |
|---|---|---:|
| 0 conocidas | `UNKNOWN` | 1.279 |
| 1 conocida | `SPECIALIST` | 89.918 |
| 2 conocidas | `MIXED` | 2.039 |
| 3 o mas conocidas | `DIVERSIFIED` | 122 |

Los thresholds solicitados son, por tanto, `1`, `2` y `3+`; cero queda aislado como
desconocido para no confundir falta de metadata con especializacion.

## Fanout y ponderaciones

Items, pagos y reviews pueden repetirse dentro de un pedido. Para construir
`mart_order_summary` se agregan por separado:

- Items: unidades, productos, sellers, GMV y flete.
- Pagos: valor pagado, filas y metodos.
- Reviews: score promedio y cantidad de filas.

Luego se unen tres tablas con una fila por pedido. Este orden evita multiplicaciones
muchos a muchos. Los marts de categoria/seller operan a nivel item; su review promedio
queda ponderada por items. Las metricas ejecutivas y de entrega operan a nivel pedido.

## Entrega y review

`delivery_delay_days` es la diferencia entre fecha entregada y fecha estimada. Un pedido
es tardio si la entrega real supera la estimada. Las 23 cronologias que tienen aprobacion
anterior a compra, entrega anterior a compra o entrega anterior al carrier se excluyen de
`mart_delivery_experience` sin corregir la fuente.

Las reviews faltantes permanecen nulas. Los promedios solo usan reviews observadas. La
diferencia `4,29` a tiempo versus `2,57` tardia es una asociacion descriptiva; variables
de producto, vendedor, geografia o seleccion de quien responde pueden confundirla.

## Cobertura y supresion

| Mart | Condicion `PUBLISHABLE` |
|---|---|
| Cruce de segmentos | Al menos 30 clientes. |
| Afinidad segmento-categoria | Al menos 30 clientes. |
| Categoria | Al menos 30 pedidos. |
| Vendedor | Al menos 30 pedidos. |
| Entrega mensual/estado | Al menos 30 pedidos. |

Los grupos menores quedan `SUPPRESSED`, no se eliminan de los CSV de control ni se
convierten a cero. El resumen unidimensional de segmentos es publicable por diseno; la
categoria `UNKNOWN` se muestra como limitacion.

## Quality gates

- `HIGH`: integridad de claves, relaciones, valores no negativos, unicidad/completitud de
  segmentos y reconciliacion de GMV. Una falla bloquea `export`.
- `MEDIUM`: problemas reales de cobertura o consistencia que se informan y no se corrigen
  silenciosamente.

El build de referencia obtuvo 11 `HIGH PASS`, 4 `MEDIUM FAIL` y 0 `HIGH FAIL`.
