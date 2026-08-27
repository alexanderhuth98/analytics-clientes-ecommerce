# Acceso a datos

## Fuente

- Titulo: `Brazilian E-Commerce Public Dataset by Olist`.
- Propietario mostrado por Kaggle: `Olist`.
- Slug: `olistbr/brazilian-ecommerce`.
- Pagina: <https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>.
- Endpoint usado: <https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce>.
- Metadata verificable: <https://www.kaggle.com/api/v1/datasets/view/olistbr/brazilian-ecommerce>.

La descripcion de Kaggle presenta datos comerciales anonimizados de aproximadamente
100.000 pedidos entre 2016 y 2018. El proyecto no afirma que la muestra represente todo
el e-commerce brasileno.

## Snapshot de referencia

`manifests/raw_sources.jsonl` registra el archivo efectivamente usado:

| Atributo | Valor |
|---|---|
| Descarga UTC | `2026-08-21T01:48:58.662756+00:00` |
| ZIP | `raw/brazilian-ecommerce.zip` |
| Bytes | `44.717.580` |
| SHA-256 | `967e41e04fc306fe604e2a693f488995a8b41e5047418f8a5c8e4abd6deca784` |
| CSV | 9 |

El hash identifica el snapshot procesado. Kaggle puede actualizar el archivo bajo el
mismo slug; una descarga futura no debe asumirse identica.

## Autenticacion

El cliente intenta la descarga publica sin credenciales. Si Kaggle exige autenticacion,
defina variables de entorno locales:

```powershell
$env:KAGGLE_USERNAME = "usuario"
$env:KAGGLE_KEY = "token"
uv run ecommerce-clientes download
```

`.env.example` documenta los nombres, pero la aplicacion no carga automaticamente un
archivo `.env`. Nunca incluya valores reales en Git, logs, issues, outputs o capturas.

## Almacenamiento

```text
data/raw/       ZIP y CSV extraidos
data/interim/   espacio local reservado
data/warehouse/ DuckDB
data/exports/   staging de exportacion
```

Toda la carpeta `data/` esta ignorada por Git. Para una reconstruccion exacta se necesita
el ZIP cuyo hash figura en el manifiesto; el repositorio por si solo no contiene raw.

## Atribucion y licencia de fuente

Atribucion recomendada:

> Brazilian E-Commerce Public Dataset by Olist, disponible en Kaggle bajo el slug
> `olistbr/brazilian-ecommerce`.

El endpoint de metadata de Kaggle, consultado el `2026-08-20`, expone
`CC BY-NC-SA 4.0` en el campo `licenseName`. Esta documentacion registra lo que publica
Kaggle en esa fecha; no sustituye la revision de los terminos vigentes ni asesoria legal.
Antes de redistribuir raw o derivados, vuelva a consultar la pagina y la metadata.

La licencia MIT de este repositorio cubre su codigo y documentacion. No convierte los
datos Olist a MIT ni elimina requisitos de atribucion, uso no comercial o share-alike que
puedan corresponder a la fuente.

## Privacidad

Aunque la fuente declara datos anonimizados, el proyecto aplica minimizacion adicional:

- No versiona filas de clientes, pedidos, pagos o reviews.
- No publica textos de review ni coordenadas detalladas.
- Los CSV de portfolio son agregados.
- Los identificadores de vendedor permanecen anonimos y no se muestran en visuales.
- Los cruces pequenos se suprimen con threshold 30.
