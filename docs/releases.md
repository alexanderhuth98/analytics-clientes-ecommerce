# Releases

## Estado

La release `v1.0.0` publica activos binarios fuera del historial Git, siguiendo el mismo
criterio que el proyecto de pricing.

## Activos de la version `v1.0.0`

- `powerbi/AnalyticsClientes.pbix`
- `outputs/analytics_clientes_ecommerce.xlsx`
- `outputs/dashboard_clientes_ecommerce.html`
- `outputs/dashboard_mobile.html`
- `outputs/release-v1.0.0/SHA256SUMS.txt`

## Contenido versionado

- Codigo, SQL y configuracion.
- Documentacion y licencia MIT.
- Manifiesto de procedencia sin credenciales.
- Informes del corte.
- Ocho CSV agregados de `portfolio_data/`.
- Dashboard de `site/`.
- Proyecto Power BI textual; el PBIX queda como activo de GitHub Release.

Raw, DuckDB, Parquet, ZIP, Excel, HTML autocontenido local, PBIX y secretos no deben
entrar al historial. Los binarios publicables se adjuntan al Release con hashes.

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

Los artefactos binarios se generan localmente y permanecen ignorados. Para preparar la
carpeta de release y hashes:

```powershell
.\scripts\package_release.ps1
```

Si la politica local exige scripts firmados:

```cmd
type scripts\package_release.ps1 | powershell.exe -NoProfile -Command -
```

Verifique `outputs/release-v1.0.0/SHA256SUMS.txt` y adjunte esos activos al Release.

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
