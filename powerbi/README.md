# Power BI

## Objetivo y audiencia

- Objetivo: sintetizar escala, mix de clientes, experiencia de entrega y calidad del build de ecommerce.
- Audiencia: dirección comercial, customer analytics, operaciones y experiencia de cliente.
- Grano: mes, segmento agregado, categoría, estado de entrega y vendedor anonimizado.
- Privacidad: no se cargan filas de cliente, pedido, pago o review; sólo los ocho CSV públicos agregados de `portfolio_data/`.
- Regla de cobertura: el pipeline excluye por fila completa todo estado distinto de `PUBLISHABLE` antes de escribir los CSV; Power BI no recibe identificadores ni métricas de grupos `SUPPRESSED`.

## Artefactos

- `AnalyticsClientes.pbip`: entrada editable del proyecto.
- `AnalyticsClientes.Report/`: definición PBIR de cuatro páginas y 26 visuales nativos.
- `AnalyticsClientes.SemanticModel/model.bim`: modelo TMSL editable con 10 tablas, 8 relaciones y 30 medidas.
- `AnalyticsClientes.pbix`: copia binaria local para publicar como activo de GitHub Release.
- `theme.json`: tema fuente `ClientesEditorial`, equivalente al lenguaje editorial del proyecto de pricing.
- `validate_pbip.ps1`: validación reproducible de JSON, fuentes, referencias PBIR y modelo TOM.

No se versionan `.pbix`, cachés `.pbi/`, extractos ni otros binarios. El PBIX se genera
localmente y se distribuye como activo de GitHub Release con hash SHA-256.

## Fuentes

| Tabla | Filas validadas | Uso |
|---|---:|---|
| `executive_monthly.csv` | 25 | Serie mensual de pedidos, GMV y experiencia. |
| `customer_segment_summary.csv` | 10 | Resumen por dimensión y etiqueta de segmentación. |
| `customer_cross_segment.csv` | 19 | Cruces anonimizados de valor, unidades y amplitud. |
| `customer_category_affinity.csv` | 146 | Afinidad agregada entre categoría y segmento de valor. |
| `category_performance.csv` | 63 | Mix, valor y review por categoría. |
| `delivery_experience.csv` | 40 | Experiencia mensual por estado de entrega. |
| `seller_performance.csv` | 627 | Desempeño agregado por vendedor anonimizado. |
| `quality_checks.csv` | 15 | Controles y advertencias del build. |

Las claves técnicas `build_id`, `segmentation_version` y `seller_id` están ocultas. El identificador de vendedor sólo se usa para un conteo distinto de vendedores publicables; ningún visual muestra detalle de vendedor. El validador falla si un CSV con `coverage_status` contiene un valor diferente de `PUBLISHABLE`.

## Parámetro de datos

`DataFolder` es un parámetro M obligatorio con valor versionado relativo:

```text
..\portfolio_data\
```

Todas las particiones usan `File.Contents(DataFolder & "archivo.csv")`. El repositorio no conserva rutas personales ni absolutas.

Si Power BI Desktop no resuelve la ruta relativa al abrir el proyecto, usar **Transformar datos > Administrar parámetros**, seleccionar `DataFolder` y elegir la carpeta local de `portfolio_data`. Evitar guardar esa ruta personal en archivos versionados; restaurar el valor relativo antes de publicar cambios.

## Modelo

`Calendario[Fecha]` es única y se genera dinámicamente desde el primer `month_start` hasta `as_of_date` usando `executive_monthly.csv`.

Relaciones activas, uno a muchos y con filtro en una dirección:

| Desde | Columna | Hacia |
|---|---|---|
| `executive_monthly` | `month_start` | `Calendario[Fecha]` |
| `delivery_experience` | `month_start` | `Calendario[Fecha]` |
| `customer_segment_summary` | `as_of_date` | `Calendario[Fecha]` |
| `customer_cross_segment` | `as_of_date` | `Calendario[Fecha]` |
| `customer_category_affinity` | `as_of_date` | `Calendario[Fecha]` |
| `category_performance` | `as_of_date` | `Calendario[Fecha]` |
| `seller_performance` | `as_of_date` | `Calendario[Fecha]` |
| `quality_checks` | `as_of_date` | `Calendario[Fecha]` |

No existen relaciones entre hechos. Las dos series mensuales se relacionan por `month_start`; los marts de corte se relacionan por `as_of_date`. Esto evita uniones por etiquetas no únicas y relaciones muchos a muchos no defendibles.

La tabla `Medidas` incluye, entre otras:

- Escala: `Pedidos`, `Pedidos entregados`, `GMV`, `Ticket promedio`.
- Clientes: `Clientes elegibles`, `Clientes alto valor`, `Share GMV alto valor`, `Clientes una categoria`.
- Mix: `GMV por segmento`, `GMV afinidad`, `GMV categorias`.
- Operación: `Tasa de entrega tardia`, `Tasa tardia publicable`, `Review a tiempo`, `Review tardia`.
- Cobertura: `Vendedores publicables`; `Filas suprimidas` permanece como control y debe ser cero en los CSV públicos.
- Calidad: `Fallas altas`, `Advertencias medias`, `Tasa controles aprobados`.

`Clientes elegibles` filtra exclusivamente la dimensión `VALUE`; sumar las tres dimensiones de `customer_segment_summary` triplicaría la población. `GMV` excluye flete y no se presenta como ingreso, margen o beneficio.

## Páginas

### Panorama ejecutivo

- KPI: pedidos, GMV entregado, clientes elegibles y tasa de entrega tardía.
- Tendencia: GMV mensual.
- Desglose: GMV por categoría publicable.

### Clientes y mix

- KPI: clientes elegibles, clientes de alto valor, share de GMV alto valor y clientes con una categoría.
- Desglose: GMV por segmento y afinidad categoría-segmento.
- Tabla: cruces de segmentación, sólo cuando son publicables.

### Operación y experiencia

- KPI: tasa tardía, review a tiempo, review tardía y vendedores publicables.
- Tendencia: tasa tardía mensual.
- Desglose: review por estado de entrega y tasa tardía por estado del vendedor.

### Calidad y cobertura

- KPI: fallas altas, advertencias medias, tasa de aprobación y filas agregadas suprimidas.
- Desglose: controles por estado.
- Tabla: severidad, estado, valor observado, umbral y detalle de cada control.

## Diseño e interacciones

- Tema `ClientesEditorial`: base marfil, azul petróleo, acento terracota y rojo reservado para alertas.
- Los visuales usan interacciones nativas y tooltips mejorados.
- Los títulos declaran cuándo una medida usa sólo cobertura publicable.
- El lienzo es 16:9 y usa tarjetas arriba, tendencias/desgloses al centro y detalle abajo cuando aplica.
- No hay visuales personalizados, slicers dedicados, drill-through ni layout móvil específico.

## Apertura y actualización

1. Abrir `powerbi\AnalyticsClientes.pbip` con Power BI Desktop.
2. Confirmar el parámetro `DataFolder` en **Transformar datos > Administrar parámetros**.
3. Seleccionar **Inicio > Actualizar**.
4. Revisar las cuatro páginas y guardar el PBIP sin rutas personales.
5. Guardar una copia `AnalyticsClientes.pbix` para GitHub Release; no commitear el binario.

## Validación reproducible

Desde la raíz del proyecto:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\powerbi\validate_pbip.ps1
```

Si una política corporativa `AllSigned` invalida `Bypass`, ejecutar el mismo validador por entrada estándar sin cambiar la política del equipo:

```powershell
cmd.exe /d /c "type powerbi\validate_pbip.ps1 | powershell.exe -NoProfile -Command -"
```

Si la detección de Power BI Desktop falla, usar `-DesktopBin` con la carpeta `bin` de la instalación local.

Validaciones ejecutadas:

- Deserialización JSON de 42 archivos, incluidos PBIP, PBIR, PBISM, `.platform` y `model.bim`.
- Deserialización TOM con Power BI Desktop `2.157.879.0`: 10 tablas, 8 relaciones, 30 medidas y un parámetro.
- Existencia y no vaciedad de los ocho CSV; encabezados y valores contrastados contra `sourceColumn` y los tipos declarados.
- Integridad de 26 referencias de campos/medidas en los visuales.
- Cuatro nombres de página exactos.
- Ausencia de rutas absolutas en `model.bim`.
- Reconciliación de control: 99.441 pedidos, R$ 13.221.498,11 de GMV, 93.358 clientes elegibles, 0 fallas `HIGH` y 4 advertencias `MEDIUM`.

## Limitación de validación

La validación automatizada comprueba estructura JSON/PBIR, referencias y deserialización del modelo con TOM. No ejecuta el motor de Power Query ni renderiza el lienzo de Power BI Desktop de forma interactiva. Por eso, la actualización de los CSV, la evaluación DAX y el render final deben confirmarse al abrir el PBIP; no se incluye una caché ni un `.pbix` para simular esa comprobación.
