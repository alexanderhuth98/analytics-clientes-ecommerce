# Operaciones

## Requisitos

- Python `>=3.11,<3.13`.
- `uv` para resolver el lockfile.
- Node.js `24` y npm para las pruebas de navegador.
- Acceso a Kaggle o un ZIP local con el hash esperado.
- Power BI Desktop solo para abrir/refrescar el proyecto PBIP; no es requisito del
  pipeline Python.

## Instalacion

```powershell
uv sync --extra dev --locked
uv run ecommerce-clientes --help
```

No use `--upgrade` en una reconstruccion del build publicado. Si se actualizan
dependencias, revise y versiona el nuevo `uv.lock` en un cambio separado.

## Etapas

```powershell
uv run ecommerce-clientes download
uv run ecommerce-clientes ingest
uv run ecommerce-clientes build --as-of 2018-10-17
uv run ecommerce-clientes validate
uv run ecommerce-clientes export
```

`all` ejecuta las cinco etapas:

```powershell
uv run ecommerce-clientes all --as-of 2018-10-17
```

`--force` vuelve a descargar o ingerir cuando la etapa lo utiliza. Antes de forzar,
conserve el manifiesto/hash del snapshot que necesita reproducir.

## Salidas esperadas

| Ruta | Resultado |
|---|---|
| `data/warehouse/ecommerce.duckdb` | Warehouse local. |
| `manifests/raw_sources.jsonl` | Procedencia del ZIP. |
| `outputs/` | Marts completos en CSV/Parquet/Excel, HTML, resumen y validacion locales. |
| `reports/<corte>/` | Informes versionables del build. |
| `portfolio_data/` | Ocho CSV publicos; solo filas `PUBLISHABLE` donde hay control de cobertura. |
| `site/` | Dashboard HTML desktop y movil renderizado desde la vista publica. |

## Validacion manual

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=ecommerce_clientes --cov-report=term-missing --cov-report=xml
uv run ecommerce-clientes validate
npm ci
npx playwright install chromium
npm run test:e2e
```

El proyecto declara `fail_under = 80` para cobertura. La CI ejecuta la misma suite y debe
permanecer roja si lint, tests, cobertura o los contratos del dashboard fallan. Playwright
levanta `site/` con un servidor local basado en `Python http.server`, prueba Chromium desktop y movil, conserva trazas
y capturas solo ante fallas y publica los diagnosticos durante 7 dias. Para probar un sitio ya
desplegado sin iniciar el servidor local, defina `E2E_BASE_URL` con la URL base terminada en `/`.

La validacion analitica si tiene evidencia publicada: 15 controles, 0 fallas `HIGH` y 4
advertencias `MEDIUM` en `reports/2018-10-17/validation_report.md`.

## CI

`ci.yml` tiene tres responsabilidades independientes:

- Calidad: instala desde `uv.lock`, ejecuta Ruff y pytest con cobertura, exporta el lock y
  lo audita con `pip-audit`.
- E2E (Chromium): instala desde `package-lock.json` y ejecuta los proyectos desktop y movil
  contra los artefactos versionados de `site/`.
- Secretos: Gitleaks revisa el historial disponible con contenido redactado.

La auditoria de dependencias y el scan de secretos reducen riesgo, pero no garantizan
ausencia de vulnerabilidades o credenciales. Un hallazgo requiere revision humana.

## GitHub Pages

`pages.yml` publica exclusivamente `site/` en pushes a `main` o por ejecucion manual. No
descarga Olist, no reconstruye el warehouse y no necesita secretos Kaggle. El dashboard
publico esta disponible en <https://alexanderhuth98.github.io/analytics-clientes-ecommerce/>;
las variantes desktop y movil declaran esa URL principal como canonical. Despues de cada
deploy, el workflow usa la URL emitida por GitHub Pages para ejecutar un smoke test de
produccion en Chromium; no comprueba la disponibilidad de Google Fonts ni GoatCounter.

El repositorio publico canonico es
`https://github.com/alexanderhuth98/analytics-clientes-ecommerce`. El remoto GitLab de la
copia de desarrollo es privado y no es un endpoint publico del paquete.

## Recuperacion

| Falla | Comportamiento | Accion |
|---|---|---|
| Descarga interrumpida | Queda `.zip.part`; el ZIP previo no se reemplaza. | Reintentar `download`; usar `--force` si el parcial persiste. |
| ZIP inseguro/incompleto | La extraccion falla antes de publicar `olist/`. | Eliminar solo el staging local y verificar fuente/hash. |
| Contrato CSV incompatible | La base staging falla; el warehouse previo se conserva. | Comparar columnas con `config.EXPECTED_COLUMNS`. |
| Build SQL fallido | DuckDB hace rollback de la transaccion. | Corregir causa y repetir `build`. |
| Gate `HIGH` fallido | `validate`/`export` bloquea publicacion. | Revisar `quality_checks`; no bajar el gate para publicar. |
| Export interrumpido | Puede existir un conjunto parcial de destinos copiados. | Repetir `export` despues de validar; revisar `export_manifest.json`. |

## Secretos y datos

- Use variables de entorno, no archivos versionados.
- No suba `.env`, ZIP, DuckDB, Parquet detallado, Excel ni PBIX.
- Revise el diff antes de publicar manifests o informes.
- Rote inmediatamente cualquier token expuesto; borrarlo en un commit posterior no lo
  elimina del historial.

## Power BI

La validacion estructural existente se ejecuta en Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\powerbi\validate_pbip.ps1
```

Ese script valida estructura y referencias, no ejecuta Power Query ni confirma el render
interactivo. La actualizacion final debe revisarse en Power BI Desktop.
