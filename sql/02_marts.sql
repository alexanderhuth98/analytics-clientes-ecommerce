DROP TABLE IF EXISTS mart_order_summary;
DROP TABLE IF EXISTS mart_executive_monthly;
DROP TABLE IF EXISTS mart_customer_segmentation_asof;
DROP TABLE IF EXISTS mart_customer_segment_summary;
DROP TABLE IF EXISTS mart_customer_cross_segment;
DROP TABLE IF EXISTS mart_customer_category_affinity;
DROP TABLE IF EXISTS mart_category_performance;
DROP TABLE IF EXISTS mart_seller_performance;
DROP TABLE IF EXISTS mart_delivery_experience;

CREATE TABLE mart_order_summary AS
WITH item_agg AS (
    SELECT
        order_id,
        COUNT(*) AS units,
        COUNT(DISTINCT product_id) AS distinct_products,
        COUNT(DISTINCT seller_id) AS distinct_sellers,
        SUM(item_value_brl) AS merchandise_gmv_brl,
        SUM(freight_value_brl) AS freight_value_brl
    FROM fct_order_item
    GROUP BY order_id
), payment_agg AS (
    SELECT
        order_id,
        SUM(payment_value_brl) AS paid_value_brl,
        COUNT(*) AS payment_rows,
        COUNT(DISTINCT payment_type) AS payment_methods
    FROM fct_payment
    GROUP BY order_id
), review_agg AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score,
        COUNT(*) AS review_rows
    FROM fct_review
    GROUP BY order_id
)
SELECT
    o.*,
    COALESCE(i.units, 0) AS units,
    COALESCE(i.distinct_products, 0) AS distinct_products,
    COALESCE(i.distinct_sellers, 0) AS distinct_sellers,
    COALESCE(i.merchandise_gmv_brl, 0) AS merchandise_gmv_brl,
    COALESCE(i.freight_value_brl, 0) AS freight_value_brl,
    COALESCE(p.paid_value_brl, 0) AS paid_value_brl,
    COALESCE(p.payment_rows, 0) AS payment_rows,
    COALESCE(p.payment_methods, 0) AS payment_methods,
    r.review_score,
    COALESCE(r.review_rows, 0) AS review_rows,
    CASE
        WHEN o.order_status = 'delivered'
         AND o.delivered_customer_at IS NOT NULL
         AND o.estimated_delivery_at IS NOT NULL
        THEN DATE_DIFF('day', o.estimated_delivery_at, o.delivered_customer_at)
    END AS delivery_delay_days,
    CASE
        WHEN o.order_status = 'delivered'
         AND o.delivered_customer_at IS NOT NULL
         AND o.estimated_delivery_at IS NOT NULL
        THEN o.delivered_customer_at > o.estimated_delivery_at
    END AS is_late
FROM fct_order o
LEFT JOIN item_agg i USING (order_id)
LEFT JOIN payment_agg p USING (order_id)
LEFT JOIN review_agg r USING (order_id);

CREATE TABLE mart_executive_monthly AS
SELECT
    b.build_id,
    b.as_of_date,
    DATE_TRUNC('month', o.purchased_at)::DATE AS month_start,
    COUNT(*) AS orders,
    COUNT(DISTINCT o.customer_unique_id) AS customers,
    COUNT(*) FILTER (WHERE o.order_status = 'delivered') AS delivered_orders,
    COUNT(*) FILTER (WHERE o.order_status IN ('canceled', 'unavailable')) AS failed_orders,
    SUM(o.merchandise_gmv_brl) FILTER (WHERE o.order_status = 'delivered') AS merchandise_gmv_brl,
    SUM(o.freight_value_brl) FILTER (WHERE o.order_status = 'delivered') AS freight_value_brl,
    SUM(o.units) FILTER (WHERE o.order_status = 'delivered') AS units,
    AVG(o.merchandise_gmv_brl) FILTER (WHERE o.order_status = 'delivered') AS avg_order_value_brl,
    AVG(o.review_score) FILTER (WHERE o.order_status = 'delivered') AS avg_review_score,
    AVG(CASE WHEN o.is_late THEN 1.0 ELSE 0.0 END)
        FILTER (WHERE o.order_status = 'delivered' AND o.is_late IS NOT NULL) AS late_delivery_rate
FROM mart_order_summary o
CROSS JOIN build_context b
WHERE o.purchased_at::DATE <= b.as_of_date
GROUP BY b.build_id, b.as_of_date, DATE_TRUNC('month', o.purchased_at)::DATE;

CREATE TABLE mart_customer_segmentation_asof AS
WITH customer_base AS (
    SELECT
        o.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS delivered_orders,
        COUNT(*) AS units,
        COUNT(DISTINCT i.product_id) AS distinct_products,
        COUNT(DISTINCT CASE WHEN p.category_name <> 'unknown' THEN p.category_name END)
            AS distinct_categories,
        SUM(i.item_value_brl) AS merchandise_gmv_brl,
        SUM(i.freight_value_brl) AS freight_value_brl
    FROM fct_order o
    JOIN fct_order_item i USING (order_id)
    LEFT JOIN dim_product p USING (product_id)
    CROSS JOIN build_context b
    WHERE o.order_status = 'delivered'
      AND o.purchased_at::DATE <= b.as_of_date
      AND i.item_value_brl >= 0
      AND o.customer_unique_id IS NOT NULL
    GROUP BY o.customer_unique_id
), value_buckets AS (
    SELECT
        merchandise_gmv_brl,
        COUNT(*) AS customers_in_tie,
        SUM(merchandise_gmv_brl) AS bucket_gmv_brl
    FROM customer_base
    GROUP BY merchandise_gmv_brl
), bucket_cumulative AS (
    SELECT
        merchandise_gmv_brl,
        (
            SUM(bucket_gmv_brl) OVER (
                ORDER BY merchandise_gmv_brl DESC
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) - bucket_gmv_brl
        ) / NULLIF(SUM(bucket_gmv_brl) OVER (), 0) AS cumulative_share_before
    FROM value_buckets
), segmented AS (
    SELECT
        c.*,
        CASE
            WHEN c.merchandise_gmv_brl <= 0 THEN 'NO_VALUE'
            WHEN v.cumulative_share_before < 0.80 THEN 'A_HIGH_VALUE'
            WHEN v.cumulative_share_before < 0.95 THEN 'B_MEDIUM_VALUE'
            ELSE 'C_LOW_VALUE'
        END AS value_segment,
        CASE
            WHEN c.units = 1 THEN 'ONE_ITEM'
            WHEN c.units BETWEEN 2 AND 3 THEN 'TWO_TO_THREE'
            ELSE 'FOUR_PLUS'
        END AS unit_segment,
        CASE
            WHEN c.distinct_categories = 0 THEN 'UNKNOWN'
            WHEN c.distinct_categories = 1 THEN 'SPECIALIST'
            WHEN c.distinct_categories = 2 THEN 'MIXED'
            ELSE 'DIVERSIFIED'
        END AS category_segment
    FROM customer_base c
    JOIN bucket_cumulative v USING (merchandise_gmv_brl)
)
SELECT
    b.build_id,
    b.as_of_date,
    b.segmentation_version,
    s.*,
    CASE WHEN s.category_segment = 'UNKNOWN' THEN 'DIRECTIONAL' ELSE 'PUBLISHABLE' END
        AS coverage_status
FROM segmented s
CROSS JOIN build_context b;

CREATE TABLE mart_customer_segment_summary AS
WITH long_segments AS (
    SELECT *, 'VALUE' AS segment_dimension, value_segment AS segment_label
    FROM mart_customer_segmentation_asof
    UNION ALL
    SELECT *, 'UNITS' AS segment_dimension, unit_segment AS segment_label
    FROM mart_customer_segmentation_asof
    UNION ALL
    SELECT *, 'CATEGORIES' AS segment_dimension, category_segment AS segment_label
    FROM mart_customer_segmentation_asof
)
SELECT
    build_id,
    as_of_date,
    segmentation_version,
    segment_dimension,
    segment_label,
    COUNT(*) AS customers,
    SUM(merchandise_gmv_brl) AS merchandise_gmv_brl,
    SUM(units) AS units,
    AVG(delivered_orders) AS avg_delivered_orders,
    AVG(distinct_categories) AS avg_distinct_categories,
    SUM(merchandise_gmv_brl) / SUM(SUM(merchandise_gmv_brl)) OVER (
        PARTITION BY segment_dimension
    ) AS gmv_share,
    'PUBLISHABLE' AS coverage_status
FROM long_segments
GROUP BY build_id, as_of_date, segmentation_version, segment_dimension, segment_label;

CREATE TABLE mart_customer_cross_segment AS
SELECT
    build_id,
    as_of_date,
    segmentation_version,
    value_segment,
    unit_segment,
    category_segment,
    COUNT(*) AS customers,
    SUM(merchandise_gmv_brl) AS merchandise_gmv_brl,
    SUM(units) AS units,
    AVG(distinct_categories) AS avg_distinct_categories,
    CASE WHEN COUNT(*) >= 30 THEN 'PUBLISHABLE' ELSE 'SUPPRESSED' END AS coverage_status
FROM mart_customer_segmentation_asof
GROUP BY build_id, as_of_date, segmentation_version, value_segment, unit_segment, category_segment;

CREATE TABLE mart_customer_category_affinity AS
SELECT
    b.build_id,
    b.as_of_date,
    s.value_segment,
    p.category_name,
    COUNT(DISTINCT o.customer_unique_id) AS customers,
    COUNT(*) AS units,
    SUM(i.item_value_brl) AS merchandise_gmv_brl,
    CASE WHEN COUNT(DISTINCT o.customer_unique_id) >= 30 THEN 'PUBLISHABLE' ELSE 'SUPPRESSED' END
        AS coverage_status
FROM fct_order o
JOIN fct_order_item i USING (order_id)
JOIN dim_product p USING (product_id)
JOIN mart_customer_segmentation_asof s USING (customer_unique_id)
CROSS JOIN build_context b
WHERE o.order_status = 'delivered'
  AND o.purchased_at::DATE <= b.as_of_date
GROUP BY b.build_id, b.as_of_date, s.value_segment, p.category_name;

CREATE TABLE mart_category_performance AS
SELECT
    b.build_id,
    b.as_of_date,
    p.category_name,
    COUNT(*) AS units,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(DISTINCT o.customer_unique_id) AS customers,
    SUM(i.item_value_brl) AS merchandise_gmv_brl,
    AVG(i.item_value_brl) AS avg_item_value_brl,
    AVG(os.review_score) AS avg_review_score,
    CASE WHEN COUNT(DISTINCT o.order_id) >= 30 THEN 'PUBLISHABLE' ELSE 'SUPPRESSED' END
        AS coverage_status
FROM fct_order o
JOIN fct_order_item i USING (order_id)
JOIN dim_product p USING (product_id)
JOIN mart_order_summary os USING (order_id)
CROSS JOIN build_context b
WHERE o.order_status = 'delivered'
  AND o.purchased_at::DATE <= b.as_of_date
GROUP BY b.build_id, b.as_of_date, p.category_name;

CREATE TABLE mart_seller_performance AS
SELECT
    b.build_id,
    b.as_of_date,
    i.seller_id,
    s.seller_state,
    COUNT(DISTINCT o.order_id) AS orders,
    COUNT(*) AS units,
    SUM(i.item_value_brl) AS merchandise_gmv_brl,
    AVG(os.review_score) AS avg_review_score,
    AVG(CASE WHEN os.is_late THEN 1.0 ELSE 0.0 END)
        FILTER (WHERE os.is_late IS NOT NULL) AS late_delivery_rate,
    CASE WHEN COUNT(DISTINCT o.order_id) >= 30 THEN 'PUBLISHABLE' ELSE 'SUPPRESSED' END
        AS coverage_status
FROM fct_order o
JOIN fct_order_item i USING (order_id)
JOIN dim_seller s USING (seller_id)
JOIN mart_order_summary os USING (order_id)
CROSS JOIN build_context b
WHERE o.order_status = 'delivered'
  AND o.purchased_at::DATE <= b.as_of_date
GROUP BY b.build_id, b.as_of_date, i.seller_id, s.seller_state;

CREATE TABLE mart_delivery_experience AS
SELECT
    b.build_id,
    b.as_of_date,
    DATE_TRUNC('month', o.purchased_at)::DATE AS month_start,
    CASE
        WHEN o.is_late THEN 'LATE'
        WHEN o.is_late = FALSE THEN 'ON_TIME'
        ELSE 'UNKNOWN'
    END AS delivery_status,
    COUNT(*) AS orders,
    AVG(o.review_score) AS avg_review_score,
    AVG(o.delivery_delay_days) AS avg_delivery_delay_days,
    COUNT(*) FILTER (WHERE o.review_score IS NOT NULL) AS reviewed_orders,
    CASE WHEN COUNT(*) >= 30 THEN 'PUBLISHABLE' ELSE 'SUPPRESSED' END AS coverage_status
FROM mart_order_summary o
CROSS JOIN build_context b
WHERE o.order_status = 'delivered'
  AND o.purchased_at::DATE <= b.as_of_date
  AND NOT COALESCE(
      o.approved_at < o.purchased_at
      OR o.delivered_customer_at < o.purchased_at
      OR o.delivered_customer_at < o.delivered_carrier_at,
      FALSE
  )
GROUP BY b.build_id, b.as_of_date, DATE_TRUNC('month', o.purchased_at)::DATE, delivery_status;
