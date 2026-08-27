# Operaciones

## Requisitos

- Python `>=3.11,<3.13`.
- `uv` para resolver el lockfile.
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
| `outputs/` | CSV, Parquet, Excel, HTML, resumen y validacion locales. |
| `reports/<corte>/` | Informes versionables del build. |
| `portfolio_data/` | Ocho CSV agregados. |
| `site/` | Dashboard HTML desktop y movil. |

## Validacion manual

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=ecommerce_clientes --cov-report=term-missing --cov-report=xml
uv run ecommerce-clientes validate
```

El proyecto declara `fail_under = 80` para cobertura y mantiene 49 pruebas versionadas.
La CI ejecuta la misma suite y debe permanecer roja si lint, tests o cobertura fallan.

La validacion analitica si tiene evidencia publicada: 15 controles, 0 fallas `HIGH` y 4
advertencias `MEDIUM` en `reports/2018-10-17/validation_report.md`.

## CI

`ci.yml` tiene dos responsabilidades:

- Calidad: instala desde `uv.lock`, ejecuta Ruff y pytest con cobertura, exporta el lock y
  lo audita con `pip-audit`.
- Secretos: Gitleaks revisa el historial disponible con contenido redactado.

La auditoria de dependencias y el scan de secretos reducen riesgo, pero no garantizan
ausencia de vulnerabilidades o credenciales. Un hallazgo requiere revision humana.

## GitHub Pages

`pages.yml` publica exclusivamente `site/` en pushes a `main` o por ejecucion manual. No
descarga Olist, no reconstruye el warehouse y no necesita secretos Kaggle. La URL solo
debe documentarse despues del primer despliegue exitoso; actualmente no se declara una.

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
