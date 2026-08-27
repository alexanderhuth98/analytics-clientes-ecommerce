DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS bridge_customer_order_address;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_seller;
DROP TABLE IF EXISTS dim_geography;
DROP TABLE IF EXISTS fct_order;
DROP TABLE IF EXISTS fct_order_item;
DROP TABLE IF EXISTS fct_payment;
DROP TABLE IF EXISTS fct_review;

CREATE TABLE dim_customer AS
SELECT
    customer_unique_id,
    COUNT(DISTINCT customer_id) AS observed_order_addresses
FROM raw_customers
WHERE NULLIF(TRIM(customer_unique_id), '') IS NOT NULL
GROUP BY customer_unique_id;

CREATE TABLE bridge_customer_order_address AS
SELECT
    customer_id,
    customer_unique_id,
    TRY_CAST(customer_zip_code_prefix AS INTEGER) AS customer_zip_code_prefix,
    NULLIF(TRIM(customer_city), '') AS customer_city,
    UPPER(NULLIF(TRIM(customer_state), '')) AS customer_state
FROM raw_customers;

CREATE TABLE dim_geography AS
SELECT
    TRY_CAST(geolocation_zip_code_prefix AS INTEGER) AS zip_code_prefix,
    MEDIAN(TRY_CAST(geolocation_lat AS DOUBLE)) AS latitude,
    MEDIAN(TRY_CAST(geolocation_lng AS DOUBLE)) AS longitude,
    MODE(NULLIF(TRIM(geolocation_city), '')) AS city,
    MODE(UPPER(NULLIF(TRIM(geolocation_state), ''))) AS state,
    COUNT(*) AS source_points
FROM raw_geolocation
WHERE TRY_CAST(geolocation_zip_code_prefix AS INTEGER) IS NOT NULL
GROUP BY TRY_CAST(geolocation_zip_code_prefix AS INTEGER);

CREATE TABLE dim_product AS
SELECT
    p.product_id,
    NULLIF(TRIM(p.product_category_name), '') AS category_name_pt,
    COALESCE(NULLIF(TRIM(t.product_category_name_english), ''), 'unknown') AS category_name,
    TRY_CAST(p.product_photos_qty AS INTEGER) AS photos_qty,
    TRY_CAST(p.product_weight_g AS DOUBLE) AS weight_g,
    TRY_CAST(p.product_length_cm AS DOUBLE) AS length_cm,
    TRY_CAST(p.product_height_cm AS DOUBLE) AS height_cm,
    TRY_CAST(p.product_width_cm AS DOUBLE) AS width_cm
FROM raw_products p
LEFT JOIN raw_product_category_name_translation t
  ON p.product_category_name = t.product_category_name;

CREATE TABLE dim_seller AS
SELECT
    seller_id,
    TRY_CAST(seller_zip_code_prefix AS INTEGER) AS seller_zip_code_prefix,
    NULLIF(TRIM(seller_city), '') AS seller_city,
    UPPER(NULLIF(TRIM(seller_state), '')) AS seller_state
FROM raw_sellers;

CREATE TABLE fct_order AS
SELECT
    o.order_id,
    a.customer_unique_id,
    o.customer_id,
    LOWER(NULLIF(TRIM(o.order_status), '')) AS order_status,
    TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchased_at,
    TRY_CAST(o.order_approved_at AS TIMESTAMP) AS approved_at,
    TRY_CAST(o.order_delivered_carrier_date AS TIMESTAMP) AS delivered_carrier_at,
    TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP) AS delivered_customer_at,
    TRY_CAST(o.order_estimated_delivery_date AS TIMESTAMP) AS estimated_delivery_at,
    a.customer_zip_code_prefix,
    a.customer_city,
    a.customer_state
FROM raw_orders o
LEFT JOIN bridge_customer_order_address a USING (customer_id);

CREATE TABLE fct_order_item AS
SELECT
    order_id,
    TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
    product_id,
    seller_id,
    TRY_CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_at,
    TRY_CAST(price AS DECIMAL(18, 2)) AS item_value_brl,
    TRY_CAST(freight_value AS DECIMAL(18, 2)) AS freight_value_brl
FROM raw_order_items;

CREATE TABLE fct_payment AS
SELECT
    order_id,
    TRY_CAST(payment_sequential AS INTEGER) AS payment_sequential,
    LOWER(NULLIF(TRIM(payment_type), '')) AS payment_type,
    TRY_CAST(payment_installments AS INTEGER) AS payment_installments,
    TRY_CAST(payment_value AS DECIMAL(18, 2)) AS payment_value_brl
FROM raw_order_payments;

CREATE TABLE fct_review AS
SELECT
    review_id,
    order_id,
    TRY_CAST(review_score AS INTEGER) AS review_score,
    NULLIF(TRIM(review_comment_title), '') AS review_comment_title,
    NULLIF(TRIM(review_comment_message), '') AS review_comment_message,
    TRY_CAST(review_creation_date AS TIMESTAMP) AS review_created_at,
    TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_answered_at
FROM raw_order_reviews;

CREATE TABLE dim_date AS
WITH bounds AS (
    SELECT
        MIN(purchased_at)::DATE AS min_date,
        MAX(purchased_at)::DATE AS max_date
    FROM fct_order
), dates AS (
    SELECT UNNEST(GENERATE_SERIES(min_date, max_date, INTERVAL 1 DAY))::DATE AS date_day
    FROM bounds
)
SELECT
    date_day,
    YEAR(date_day) AS year,
    MONTH(date_day) AS month_number,
    STRFTIME(date_day, '%Y-%m') AS year_month,
    DATE_TRUNC('month', date_day)::DATE AS month_start,
    QUARTER(date_day) AS quarter_number,
    DAYOFWEEK(date_day) AS weekday_number
FROM dates;
