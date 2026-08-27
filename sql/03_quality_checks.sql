DROP TABLE IF EXISTS quality_checks;

CREATE TABLE quality_checks AS
WITH checks AS (
    SELECT
        'orders_pk_unique' AS check_id,
        'HIGH' AS severity,
        COUNT(*) - COUNT(DISTINCT order_id) AS observed_value,
        0::DOUBLE AS threshold,
        'order_id debe ser unico en fct_order' AS details
    FROM fct_order
    UNION ALL
    SELECT 'customers_bridge_pk_unique', 'HIGH', COUNT(*) - COUNT(DISTINCT customer_id), 0,
           'customer_id debe ser unico en el puente pedido-cliente'
    FROM bridge_customer_order_address
    UNION ALL
    SELECT 'order_items_pk_unique', 'HIGH', COUNT(*) - COUNT(DISTINCT order_id || ':' || order_item_id), 0,
           'order_id + order_item_id debe ser unico'
    FROM fct_order_item
    UNION ALL
    SELECT 'orders_without_customer', 'HIGH', COUNT(*) FILTER (WHERE customer_unique_id IS NULL), 0,
           'Todo pedido debe resolver customer_unique_id'
    FROM fct_order
    UNION ALL
    SELECT 'items_without_order', 'HIGH', COUNT(*) FILTER (WHERE o.order_id IS NULL), 0,
           'Todo item debe resolver un pedido'
    FROM fct_order_item i LEFT JOIN fct_order o USING (order_id)
    UNION ALL
    SELECT 'items_without_product', 'HIGH', COUNT(*) FILTER (WHERE p.product_id IS NULL), 0,
           'Todo item debe resolver un producto'
    FROM fct_order_item i LEFT JOIN dim_product p USING (product_id)
    UNION ALL
    SELECT 'items_without_seller', 'HIGH', COUNT(*) FILTER (WHERE s.seller_id IS NULL), 0,
           'Todo item debe resolver un vendedor'
    FROM fct_order_item i LEFT JOIN dim_seller s USING (seller_id)
    UNION ALL
    SELECT 'negative_item_values', 'HIGH', COUNT(*) FILTER (WHERE item_value_brl < 0), 0,
           'Los importes de item no pueden ser negativos'
    FROM fct_order_item
    UNION ALL
    SELECT 'invalid_order_chronology_source', 'MEDIUM', COUNT(*) FILTER (
               WHERE approved_at < purchased_at
                  OR delivered_customer_at < purchased_at
                  OR delivered_customer_at < delivered_carrier_at
           ), 0, 'Filas excluidas de metricas operativas; el dato fuente no se corrige'
    FROM fct_order
    UNION ALL
    SELECT 'customer_segment_unique', 'HIGH', COUNT(*) - COUNT(DISTINCT customer_unique_id), 0,
           'Cada cliente elegible debe tener una sola segmentacion'
    FROM mart_customer_segmentation_asof
    UNION ALL
    SELECT 'customer_segment_complete', 'HIGH', COUNT(*) FILTER (
               WHERE value_segment IS NULL OR unit_segment IS NULL OR category_segment IS NULL
           ), 0, 'Las tres dimensiones de segmentacion son obligatorias'
    FROM mart_customer_segmentation_asof
    UNION ALL
    SELECT 'customer_gmv_reconciliation', 'HIGH', ABS(
               (SELECT SUM(merchandise_gmv_brl) FROM mart_customer_segmentation_asof) -
               (SELECT SUM(i.item_value_brl)
                  FROM fct_order o
                  JOIN fct_order_item i USING (order_id)
                  CROSS JOIN build_context b
                 WHERE o.order_status = 'delivered'
                   AND o.purchased_at::DATE <= b.as_of_date
                   AND i.item_value_brl >= 0
                   AND o.customer_unique_id IS NOT NULL)
           ), 0.01, 'El GMV segmentado debe reconciliar con items elegibles'
    UNION ALL
    SELECT 'unknown_product_categories', 'MEDIUM', COUNT(*) FILTER (WHERE category_name = 'unknown'), 0,
           'Categorias sin traduccion o clasificacion'
    FROM dim_product
    UNION ALL
    SELECT 'orders_payment_difference_gt_1', 'MEDIUM', COUNT(*) FILTER (
               WHERE ABS(paid_value_brl - merchandise_gmv_brl - freight_value_brl) > 1
                 AND order_status NOT IN ('canceled', 'unavailable')
           ), 0, 'Diferencias pueden incluir vouchers y ajustes; se informan, no se imputan'
    FROM mart_order_summary
    UNION ALL
    SELECT 'orders_without_review', 'MEDIUM', COUNT(*) FILTER (
               WHERE order_status = 'delivered' AND review_rows = 0
           ), 0, 'Pedidos entregados sin review'
    FROM mart_order_summary
)
SELECT
    b.build_id,
    b.as_of_date,
    check_id,
    severity,
    CASE WHEN observed_value <= threshold THEN 'PASS' ELSE 'FAIL' END AS status,
    observed_value,
    threshold,
    details
FROM checks
CROSS JOIN build_context b;
