# Informe de validacion

**Build:** `4877d616-bad1-48d6-bffb-17005001d164`  
**Corte:** `2018-10-17`  
**Controles:** `15`  
**Fallas altas:** `0`  
**Advertencias medias:** `4`

## Resultado

El build supera los controles bloqueantes y puede publicarse.

## Controles

| Control | Severidad | Estado | Observado | Umbral |
|---|---:|---:|---:|---:|
| `customer_gmv_reconciliation` | HIGH | PASS | 0.00 | 0.01 |
| `customer_segment_complete` | HIGH | PASS | 0.00 | 0.00 |
| `customer_segment_unique` | HIGH | PASS | 0.00 | 0.00 |
| `customers_bridge_pk_unique` | HIGH | PASS | 0.00 | 0.00 |
| `items_without_order` | HIGH | PASS | 0.00 | 0.00 |
| `items_without_product` | HIGH | PASS | 0.00 | 0.00 |
| `items_without_seller` | HIGH | PASS | 0.00 | 0.00 |
| `negative_item_values` | HIGH | PASS | 0.00 | 0.00 |
| `order_items_pk_unique` | HIGH | PASS | 0.00 | 0.00 |
| `orders_pk_unique` | HIGH | PASS | 0.00 | 0.00 |
| `orders_without_customer` | HIGH | PASS | 0.00 | 0.00 |
| `invalid_order_chronology_source` | MEDIUM | FAIL | 23.00 | 0.00 |
| `orders_payment_difference_gt_1` | MEDIUM | FAIL | 256.00 | 0.00 |
| `orders_without_review` | MEDIUM | FAIL | 646.00 | 0.00 |
| `unknown_product_categories` | MEDIUM | FAIL | 623.00 | 0.00 |

## Criterio

Las fallas `HIGH` bloquean la publicacion. Las fallas `MEDIUM` permanecen visibles como limitaciones y no se corrigen silenciosamente.
