# Documentacion

Este indice separa decisiones metodologicas, resultados y operacion para que el caso se
pueda revisar sin depender del dashboard o del warehouse local.

| Documento | Proposito |
|---|---|
| [Arquitectura](architecture.md) | Flujo, capas, granos, linaje y limites de publicacion. |
| [Acceso a datos](data_access.md) | Fuente, autenticacion, snapshot, licencia y privacidad. |
| [Metodologia](methodology.md) | Poblacion, metricas, ABC, thresholds y fanout. |
| [Diccionario](data_dictionary.md) | Campos de fuentes, modelo interno y CSV publicos. |
| [Limpieza](cleaning_log.md) | Cambios aplicados y problemas conservados. |
| [EDA](eda.md) | Hallazgos reales del build de referencia. |
| [Operaciones](operations.md) | Instalacion, pipeline, controles, CI y recuperacion. |
| [SQL highlights](sql_highlights.md) | Patrones SQL centrales y su razon analitica. |
| [Releases](releases.md) | Checklist para versionar y distribuir artefactos. |

## Orden sugerido

1. Leer `README.md` para alcance y resultados.
2. Revisar `methodology.md` antes de interpretar segmentos.
3. Contrastar hallazgos en `eda.md` con `portfolio_data/`.
4. Usar `data_dictionary.md` y `sql_highlights.md` para revision tecnica.
5. Ejecutar el flujo con `operations.md`.

## Evidencia del corte

- Build: `4877d616-bad1-48d6-bffb-17005001d164`.
- Corte: `2018-10-17`.
- Fuente procesada: 9 tablas y `1.550.922` filas.
- Exportacion publica: 8 CSV y `945` filas agregadas con cobertura publicable.
- Calidad: 15 controles, 0 fallas `HIGH`, 4 advertencias `MEDIUM`.
- Informes: `reports/2018-10-17/`.

Las cifras de esta documentacion corresponden a ese build. Un nuevo snapshot o corte
requiere regenerar resultados y actualizar la evidencia; no debe conservarse una cifra
historica como si describiera el nuevo build.
