# Analisis exploratorio

## Alcance

Resultados del build `4877d616-bad1-48d6-bffb-17005001d164`, corte `2018-10-17`.
Todas las conclusiones son descriptivas y se apoyan en los marts exportados.

## Escala y tiempo

| Metrica | Resultado |
|---|---:|
| Pedidos fuente | 99.441 |
| Clientes anonimos distintos | 96.096 |
| Pedidos entregados | 96.478 |
| Unidades entregadas | 110.197 |
| Clientes elegibles para segmentacion | 93.358 |
| GMV de mercaderia entregada | R$ 13.221.498,11 |

El rango de compra observado va de `2016-09-04` a `2018-10-17`. Los extremos incluyen
meses parciales y no son comparables con meses completos. El mayor GMV mensual observado
fue noviembre de 2017, con `R$ 987.765,37` y `7.289` pedidos entregados.

## Concentracion de valor

| Segmento | Clientes | Share clientes | Share GMV |
|---|---:|---:|---:|
| A | 42.747 | 45,8% | 80,55% |
| B | 27.659 | 29,6% | 14,45% |
| C | 22.952 | 24,6% | 5,00% |

La concentracion es material, pero A contiene casi la mitad de la base elegible. No debe
leerse como un pequeno grupo VIP: el corte se hace sobre share acumulado de GMV y respeta
empates. Tampoco existe evidencia de margen o propension futura.

## Volumen y amplitud

- `81.748` clientes (`87,6%`) compraron una sola unidad.
- `10.443` compraron `2-3` y `1.167` compraron `4+`.
- `89.918` clientes (`96,3%`) tuvieron una sola categoria conocida.
- Solo `2.039` tuvieron dos categorias y `122` tuvieron tres o mas.
- `1.279` no tuvieron ninguna categoria conocida y quedan `UNKNOWN`.

La baja amplitud y el promedio cercano a un pedido por cliente hacen razonable analizar
cross-selling, pero no sostienen una afirmacion de fidelidad. La categoria especialista
puede reflejar una unica compra, no preferencia estable.

## Categorias

Top cinco categorias publicables por GMV:

| Categoria | GMV (R$) | Pedidos | Clientes | Review media por item |
|---|---:|---:|---:|---:|
| `health_beauty` | 1.233.131,72 | 8.647 | 8.498 | 4,19 |
| `watches_gifts` | 1.166.176,98 | 5.495 | 5.421 | 4,07 |
| `bed_bath_table` | 1.023.434,76 | 9.272 | 9.008 | 3,92 |
| `sports_leisure` | 954.852,55 | 7.530 | 7.341 | 4,17 |
| `computers_accessories` | 888.724,61 | 6.530 | 6.405 | 3,99 |

Hay 63 categorias publicables y 9 suprimidas por tener menos de 30 pedidos. La categoria
`unknown` sigue visible y publicable por volumen; ocultarla subestimaria GMV y cobertura.

## Entrega y experiencia

En estratos mensuales publicables:

| Estado | Pedidos | Pedidos con review | Review ponderada |
|---|---:|---:|---:|
| A tiempo | 88.620 | 88.139 | 4,29 |
| Tardia | 7.799 | 7.636 | 2,57 |

La brecha de `1,73` puntos es consistente con una peor experiencia observada cuando hay
demora. No establece que la demora sea la unica causa: el diseno no controla producto,
seller, geografia, severidad del atraso ni sesgo de respuesta.

## Cobertura

- Vendedores: 627 publicables y 2.343 suprimidos con threshold de 30 pedidos.
- Cruces de segmentacion: 19 filas publicables y 10 suprimidas.
- Afinidades segmento-categoria: 146 filas publicables y 65 suprimidas.
- Categorias: 63 publicables y 9 suprimidas.

La mayoria de los sellers no supera el threshold. Por eso no se publica un ranking
exhaustivo ni se presenta la ausencia de un seller como rendimiento cero.

## Calidad y anomalias

| Control | Observado | Implicacion |
|---|---:|---|
| Cronologia invalida | 23 | Metricas operativas excluyen esas filas. |
| Diferencia de pago mayor a R$ 1 | 256 | Pago y GMV no se fuerzan a reconciliar. |
| Entregado sin review | 646 | El promedio se calcula sobre reviews disponibles. |
| Producto sin categoria | 623 | Se mantiene el grupo `unknown`. |

Los 11 gates `HIGH` pasaron. Las cuatro anomalias `MEDIUM` no se esconden y limitan la
interpretacion, aunque no comprometen claves, relaciones o reconciliacion de GMV.

## Conclusiones conservadoras

1. El valor historico esta concentrado, pero el segmento A es amplio y no equivale a
   rentabilidad o potencial futuro.
2. La compra observada es predominantemente de una unidad y una categoria; una estrategia
   de cross-selling es una hipotesis a probar, no un impacto demostrado.
3. `health_beauty` lidera el GMV publicable del corte.
4. Las entregas tardias presentan reviews sensiblemente menores, sin evidencia causal.
5. La cobertura limita comparaciones finas de sellers y cruces; la supresion debe
   mantenerse en cualquier visual o reporte derivado.
