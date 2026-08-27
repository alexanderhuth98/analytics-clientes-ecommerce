# Releases

## Estado

No se documenta una release ni una URL publica existente. Este archivo define el proceso
para una futura publicacion sin afirmar que ya ocurrio.

## Contenido versionado

- Codigo, SQL y configuracion.
- Documentacion y licencia MIT.
- Manifiesto de procedencia sin credenciales.
- Informes del corte.
- Ocho CSV agregados de `portfolio_data/`.
- Dashboard de `site/`.
- Proyecto Power BI textual, sin PBIX ni cache.

Raw, DuckDB, Parquet, ZIP, Excel, HTML autocontenido local, PBIX y secretos no deben
entrar al historial.

## Checklist previo

1. Confirmar el SHA-256 y la lista de archivos de `raw_sources.jsonl`.
2. Ejecutar `uv sync --extra dev --locked`.
3. Reconstruir con un `--as-of` explicito.
4. Confirmar `0` fallas `HIGH` y revisar cada advertencia `MEDIUM`.
5. Ejecutar Ruff y pytest con cobertura; no publicar como validado si no pasan.
6. Comparar conteos y GMV con el informe y los CSV de portfolio.
7. Ejecutar el validador PBIP y refrescar manualmente en Desktop si se distribuye Power BI.
8. Confirmar que `portfolio_data/` y `site/` no contengan filas, identificadores ni
   metricas de grupos `SUPPRESSED`.
9. Ejecutar auditoria de dependencias y scan de secretos.
10. Verificar nuevamente la atribucion y licencia expuesta por Kaggle.
11. Revisar que README y docs indiquen el nuevo build/corte.

## Empaquetado local

Los artefactos binarios potenciales se generan en `outputs/` y permanecen ignorados. Para
crear hashes en PowerShell:

```powershell
Get-FileHash .\outputs\analytics_clientes_ecommerce.xlsx -Algorithm SHA256
Get-FileHash .\outputs\dashboard_clientes_ecommerce.html -Algorithm SHA256
Get-FileHash .\outputs\dashboard_mobile.html -Algorithm SHA256
```

Registre los hashes junto con la release. No se declara que este paso este automatizado.

## Versionado

- Use versionado semantico para codigo/pipeline.
- Incluya el corte en el titulo o notas de la release.
- Diferencie version de codigo, `schema_version`, `segmentation_version`, `build_id` y
  `as_of_date`; no son intercambiables.
- No reutilice un tag para un snapshot distinto.

## Notas minimas

- Fuente y SHA-256 del snapshot.
- Build, corte y versiones de esquema/segmentacion.
- Conteos principales y estado de quality gates.
- Cuatro advertencias conocidas o las que correspondan al nuevo build.
- Comandos de reproduccion.
- Lista y SHA-256 de activos binarios.
- Licencia MIT del proyecto y licencia/terminos de fuente verificados en ese momento.
- Limitaciones y cualquier cambio de metodologia.

## GitHub Pages

Pages publica `site/` mediante `pages.yml`. El workflow no regenera datos. Antes de
publicar, compare el HTML con el mismo `build_id`/corte de los CSV y reportes. Agregue la
URL al README solo despues de un despliegue exitoso y verificable.
