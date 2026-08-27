# E-commerce customer analytics

Reproducible analytics case built on the **Brazilian E-Commerce Public Dataset by
Olist**. It models customer value, item volume, category breadth and delivery experience
with DuckDB and SQL, then publishes aggregate portfolio datasets, reports and dashboards.

**Reference build:** `4877d616-bad1-48d6-bffb-17005001d164`  
**As-of date:** `2018-10-17`

## Verified results

| Area | Result |
|---|---|
| Scale | `93,358` eligible customers and `R$ 13,221,498.11` in delivered merchandise GMV. |
| ABC | Group A contains `42,747` customers and `80.6%` of eligible GMV. |
| Breadth | `89,918` customers purchased from one known category. |
| Category | `health_beauty` leads publishable categories with `R$ 1,233,131.72`. |
| Delivery | Weighted review is `4.29` on time versus `2.57` late. |
| Quality | `0` failed `HIGH` checks and `4` visible `MEDIUM` warnings. |

ABC uses cumulative GMV before tied buckets: A `<80%`, B `<95%`, C otherwise. Item
segments are `1`, `2-3` and `4+`; known-category segments are `1`, `2` and `3+`.
`customer_id` is order/address scoped, while `customer_unique_id` is the analytical
customer key. One-to-many items, payments and reviews are aggregated before order-level
joins to prevent fanout.

The four warnings cover 23 invalid source chronologies, 256 payment reconciliation
differences above R$ 1, 646 delivered orders without review and 623 products without a
usable category. They are reported rather than silently repaired.

## Run

```powershell
uv sync --extra dev --locked
uv run ecommerce-clientes all --as-of 2018-10-17
```

See the [documentation index](docs/README.md), [methodology](docs/methodology.md),
[data access](docs/data_access.md) and [operations guide](docs/operations.md).

The repository includes 49 tests. CI enforces Ruff, pytest with the declared 80% coverage
threshold, dependency auditing and secret scanning.

Project code and documentation are MIT licensed. The Kaggle metadata endpoint reported
`CC BY-NC-SA 4.0` for the source on `2026-08-20`; verify the current source terms before
redistributing data. MIT does not relicense the Olist dataset.
