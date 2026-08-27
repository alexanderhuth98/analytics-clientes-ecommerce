# SQL highlights

Las consultas completas estan en `sql/`. Estos extractos muestran las decisiones que mas
afectan la validez analitica.

## 1. Identidad estable y puente de direccion

```sql
CREATE TABLE dim_customer AS
SELECT
    customer_unique_id,
    COUNT(DISTINCT customer_id) AS observed_order_addresses
FROM raw_customers
WHERE NULLIF(TRIM(customer_unique_id), '') IS NOT NULL
GROUP BY customer_unique_id;
```

La dimension usa `customer_unique_id`; el puente separado conserva `customer_id` y la
direccion de cada pedido. Asi no se modela una direccion historica como atributo fijo del
cliente.

## 2. Fanout controlado por pedido

```sql
WITH item_agg AS (
    SELECT order_id,
           COUNT(*) AS units,
           SUM(item_value_brl) AS merchandise_gmv_brl
    FROM fct_order_item
    GROUP BY order_id
), payment_agg AS (
    SELECT order_id,
           SUM(payment_value_brl) AS paid_value_brl,
           COUNT(*) AS payment_rows
    FROM fct_payment
    GROUP BY order_id
), review_agg AS (
    SELECT order_id,
           AVG(review_score) AS review_score,
           COUNT(*) AS review_rows
    FROM fct_review
    GROUP BY order_id
)
SELECT o.*, i.units, i.merchandise_gmv_brl,
       p.paid_value_brl, r.review_score
FROM fct_order o
LEFT JOIN item_agg i USING (order_id)
LEFT JOIN payment_agg p USING (order_id)
LEFT JOIN review_agg r USING (order_id);
```

Cada CTE produce una fila por pedido antes de la union. Es la proteccion central contra
la multiplicacion item x pago x review.

## 3. ABC que respeta empates

```sql
WITH value_buckets AS (
    SELECT merchandise_gmv_brl,
           SUM(merchandise_gmv_brl) AS bucket_gmv_brl
    FROM customer_base
    GROUP BY merchandise_gmv_brl
), bucket_cumulative AS (
    SELECT merchandise_gmv_brl,
           (
               SUM(bucket_gmv_brl) OVER (
                   ORDER BY merchandise_gmv_brl DESC
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) - bucket_gmv_brl
           ) / NULLIF(SUM(bucket_gmv_brl) OVER (), 0)
             AS cumulative_share_before
    FROM value_buckets
)
SELECT CASE
           WHEN cumulative_share_before < 0.80 THEN 'A_HIGH_VALUE'
           WHEN cumulative_share_before < 0.95 THEN 'B_MEDIUM_VALUE'
           ELSE 'C_LOW_VALUE'
       END AS value_segment
FROM bucket_cumulative;
```

El acumulado anterior mantiene juntos los clientes con igual GMV. El resultado puede
superar levemente 80% o 95%; dividir empates para alcanzar una cifra exacta seria
arbitrario.

## 4. Tres dimensiones explicitas

```sql
CASE
    WHEN units = 1 THEN 'ONE_ITEM'
    WHEN units BETWEEN 2 AND 3 THEN 'TWO_TO_THREE'
    ELSE 'FOUR_PLUS'
END AS unit_segment,
CASE
    WHEN distinct_categories = 0 THEN 'UNKNOWN'
    WHEN distinct_categories = 1 THEN 'SPECIALIST'
    WHEN distinct_categories = 2 THEN 'MIXED'
    ELSE 'DIVERSIFIED'
END AS category_segment
```

Los thresholds quedan versionados en SQL: unidades `1/2-3/4+` y categorias conocidas
`1/2/3+`, con cero separado por calidad.

## 5. Supresion por cobertura

```sql
CASE
    WHEN COUNT(DISTINCT o.customer_unique_id) >= 30 THEN 'PUBLISHABLE'
    ELSE 'SUPPRESSED'
END AS coverage_status
```

La afinidad exige 30 clientes. Otros marts usan el mismo numero con pedidos o clientes
segun su grano. Las filas suprimidas se conservan para auditar cobertura, pero no deben
entrar en rankings.

## 6. Cronologia invalida sin reparacion

```sql
WHERE o.order_status = 'delivered'
  AND NOT COALESCE(
      o.approved_at < o.purchased_at
      OR o.delivered_customer_at < o.purchased_at
      OR o.delivered_customer_at < o.delivered_carrier_at,
      FALSE
  )
```

Las 23 filas invalidas se excluyen solo del mart de experiencia. El control conserva el
conteo y el hecho base permanece sin alteracion.

## 7. Reconciliacion bloqueante

```sql
SELECT ABS(
    (SELECT SUM(merchandise_gmv_brl)
       FROM mart_customer_segmentation_asof) -
    (SELECT SUM(i.item_value_brl)
       FROM fct_order o
       JOIN fct_order_item i USING (order_id)
      WHERE o.order_status = 'delivered'
        AND i.item_value_brl >= 0
        AND o.customer_unique_id IS NOT NULL)
) AS observed_value;
```

El threshold es R$ `0,01`. En el build publicado la diferencia fue `0,00`, por lo que la
segmentacion reconcilia con el universo elegible.
