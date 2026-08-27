# Datos de portfolio

CSV agregados y anonimizados utilizados por Power BI y el dashboard. No se publican filas de
clientes, pedidos, pagos o reviews. Cada archivo incluye `build_id` y fecha de corte cuando aplica.

Esta carpeta es la frontera publica: en las tablas con `coverage_status` solo se incluyen
filas `PUBLISHABLE`. Los grupos con menos de 30 clientes o pedidos, segun el mart, se
excluyen por fila completa junto con sus etiquetas/identificadores y metricas; no se
publican como `SUPPRESSED` ni se reemplazan por cero. Los marts completos permanecen solo
en `outputs/`, que Git ignora.

This directory is the public boundary: tables with `coverage_status` include only
`PUBLISHABLE` rows. Groups below the mart's threshold of 30 customers or orders are
removed as complete rows, including labels/identifiers and metrics; they are neither
published as `SUPPRESSED` nor replaced with zero. Complete marts remain only in the
Git-ignored `outputs/` directory.
