import argparse
from datetime import date

from .build import build_analytics
from .download import download_all
from .export import export_all
from .ingest import ingest_all
from .validate import validate


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline de clientes, mix de compra y operacion e-commerce con Olist."
    )
    parser.add_argument(
        "stage",
        choices=["download", "ingest", "build", "validate", "export", "all"],
        help="Etapa que se desea ejecutar.",
    )
    parser.add_argument("--force", action="store_true", help="Reemplaza artefactos existentes.")
    parser.add_argument(
        "--as-of", type=date.fromisoformat, help="Fecha de corte reproducible YYYY-MM-DD."
    )
    arguments = parser.parse_args()

    if arguments.stage in ("download", "all"):
        download_all(force=arguments.force)
    if arguments.stage in ("ingest", "all"):
        ingest_all(force=arguments.force)
    if arguments.stage in ("build", "all"):
        build_analytics(as_of=arguments.as_of)
    if arguments.stage in ("validate", "all"):
        validate()
    if arguments.stage in ("export", "all"):
        export_all()


if __name__ == "__main__":
    main()
