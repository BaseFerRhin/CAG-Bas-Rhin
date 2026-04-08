"""CLI entry point: python -m src [extract|geocode|export|stats]."""

from __future__ import annotations

import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.group()
def cli() -> None:
    """CAG 67/1 — Extraction et analyse."""


@cli.command()
@click.option("--pdf", required=True, type=click.Path(exists=True, path_type=Path),
              help="Chemin vers CAG Bas-Rhin.pdf")
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def extract(pdf: Path, config: Path) -> None:
    """Extraire toutes les notices du PDF vers DuckDB."""
    from .extraction.pipeline import run_extraction
    import yaml

    cfg = yaml.safe_load(config.read_text()) if config.exists() else {}
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))
    page_start = cfg.get("page_range", {}).get("start", 154)
    page_end = cfg.get("page_range", {}).get("end", 660)

    console.print(f"[bold]Extraction CAG 67/1[/bold] — {pdf.name}")
    console.print(f"  Pages {page_start}–{page_end} → {db_path}")

    stats = run_extraction(
        pdf_path=pdf,
        db_path=db_path,
        page_range=(page_start, page_end),
        source_label=cfg.get("source_label", "cag_67"),
    )

    console.print(f"\n[green]Terminé[/green]")
    console.print(f"  Communes : {stats['communes']}")
    console.print(f"  Notices  : {stats['notices']}")
    console.print(f"  Fer      : {stats['fer_notices']}")


@cli.command()
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def geocode(config: Path) -> None:
    """Géocoder les communes (centroïdes BAN)."""
    import yaml

    cfg = yaml.safe_load(config.read_text()) if config.exists() else {}
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))

    console.print(f"[bold]Géocodage communes[/bold] — {db_path}")

    from .storage.queries import geocode_communes
    count = geocode_communes(db_path)
    console.print(f"[green]{count} communes géocodées[/green]")


@cli.command(name="export")
@click.option("--format", "fmt", default="raw-records", type=click.Choice(["raw-records", "csv", "geojson"]))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def export_cmd(fmt: str, output: Path, config: Path) -> None:
    """Exporter les notices Fer pour le pipeline parent."""
    import yaml

    cfg = yaml.safe_load(config.read_text()) if config.exists() else {}
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))

    from .export.to_raw_records import export_raw_records
    count = export_raw_records(db_path, output, fmt)
    console.print(f"[green]{count} records exportés → {output}[/green]")


@cli.command()
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def stats(config: Path) -> None:
    """Afficher les statistiques de la base."""
    import yaml

    cfg = yaml.safe_load(config.read_text()) if config.exists() else {}
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))

    from .storage.queries import get_summary_stats
    s = get_summary_stats(db_path)

    console.print(f"\n[bold]CAG 67/1 — Statistiques[/bold]")
    console.print(f"  Communes     : {s['communes']}")
    console.print(f"  Notices      : {s['notices']}")
    console.print(f"  Notices Fer  : {s['fer_notices']}")
    console.print(f"  Géocodées    : {s['geocoded']}")
    console.print(f"\n  Par type :")
    for t, c in s["by_type"]:
        console.print(f"    {t:20s} {c}")
    console.print(f"\n  Par période :")
    for p, c in s["by_periode"]:
        console.print(f"    {p:20s} {c}")


if __name__ == "__main__":
    cli()
