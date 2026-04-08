"""CLI entry point: python -m src [extract|geocode|export|stats|eda]."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _load_cfg(config: Path) -> dict:
    import yaml
    return yaml.safe_load(config.read_text()) if config.exists() else {}


@click.group()
def cli() -> None:
    """CAG 67/1 — Extraction et analyse."""


@cli.command()
@click.option("--pdf", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def extract(pdf: Path, config: Path) -> None:
    """Extraire toutes les notices du PDF vers DuckDB."""
    from .extraction.pipeline import run_extraction

    cfg = _load_cfg(config)
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))
    page_start = cfg.get("page_range", {}).get("start", 154)
    page_end = cfg.get("page_range", {}).get("end", 660)

    console.print(f"[bold]Extraction CAG 67/1[/bold] — {pdf.name}")
    console.print(f"  Pages {page_start}–{page_end} → {db_path}")

    run_extraction(
        pdf_path=pdf,
        db_path=db_path,
        page_range=(page_start, page_end),
        source_label=cfg.get("source_label", "cag_67"),
    )


@cli.command()
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def geocode(config: Path) -> None:
    """Géocoder les communes (centroïdes BAN)."""
    cfg = _load_cfg(config)
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))
    geo_cfg = cfg.get("geocoding", {})
    cache_path = Path(geo_cfg.get("cache_path", "data/communes_geo.json"))
    throttle = geo_cfg.get("throttle_rps", 10)

    console.print(f"[bold]Géocodage communes[/bold] — {db_path}")

    from .storage.queries import geocode_communes
    count = geocode_communes(db_path, cache_path=cache_path, throttle_rps=throttle)
    console.print(f"[green]{count} communes géocodées[/green]")


@cli.command(name="export")
@click.option("--format", "fmt", default="raw-records", type=click.Choice(["raw-records"]))
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path))
@click.option("--all", "export_all", is_flag=True, default=False, help="Exporter toutes les notices (pas uniquement Fer)")
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def export_cmd(fmt: str, output: Path, export_all: bool, config: Path) -> None:
    """Exporter les notices pour le pipeline parent."""
    cfg = _load_cfg(config)
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))

    from .export.to_raw_records import export_raw_records
    count = export_raw_records(db_path, output, iron_age_only=not export_all)
    console.print(f"[green]{count} records exportés → {output}[/green]")


@cli.command()
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def stats(config: Path) -> None:
    """Afficher les statistiques de la base."""
    cfg = _load_cfg(config)
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))

    from .storage.queries import get_summary_stats
    s = get_summary_stats(db_path)

    console.print(f"\n[bold]CAG 67/1 — Statistiques[/bold]")
    tbl = Table(show_header=False, box=None)
    tbl.add_column(style="bold")
    tbl.add_column(style="green")
    tbl.add_row("Communes", str(s["communes"]))
    tbl.add_row("Notices", str(s["notices"]))
    tbl.add_row("Notices Fer", str(s["fer_notices"]))
    tbl.add_row("Figures", str(s["figures"]))
    tbl.add_row("Géocodées", str(s["geocoded"]))
    console.print(tbl)

    console.print(f"\n[bold]Par type (Fer) :[/bold]")
    for t, c in s["by_type"]:
        console.print(f"  {t:20s} {c}")
    console.print(f"\n[bold]Par période (Fer) :[/bold]")
    for p, c in s["by_periode"]:
        console.print(f"  {p:20s} {c}")


@cli.command()
@click.option("--config", default="config.yaml", type=click.Path(path_type=Path))
def eda(config: Path) -> None:
    """EDA rapide post-extraction : distributions et outliers."""
    cfg = _load_cfg(config)
    db_path = Path(cfg.get("db_path", "data/cag67.duckdb"))

    from .storage.queries import extraction_metrics
    import duckdb

    m = extraction_metrics(db_path)

    console.print(f"\n[bold]EDA — CAG 67/1[/bold]")
    tbl = Table(show_header=False, box=None)
    tbl.add_column(style="bold")
    tbl.add_column(style="green")
    for k, v in m.items():
        tbl.add_row(k.replace("_", " ").title(), str(v))
    console.print(tbl)

    con = duckdb.connect(str(db_path), read_only=True)

    console.print(f"\n[bold]Distribution notices/commune (top 10) :[/bold]")
    dist = con.execute(
        "SELECT c.commune_name, COUNT(n.notice_id) as cnt "
        "FROM communes c LEFT JOIN notices n ON c.commune_id = n.commune_id "
        "GROUP BY c.commune_name ORDER BY cnt DESC LIMIT 10"
    ).fetchall()
    for name, cnt in dist:
        bar = "█" * min(cnt, 50)
        console.print(f"  {name:25s} {cnt:4d} {bar}")

    console.print(f"\n[bold]Distribution longueur texte :[/bold]")
    buckets = con.execute("""
        SELECT
            CASE
                WHEN LENGTH(full_text) < 100 THEN '<100'
                WHEN LENGTH(full_text) < 500 THEN '100-500'
                WHEN LENGTH(full_text) < 1000 THEN '500-1k'
                WHEN LENGTH(full_text) < 5000 THEN '1k-5k'
                ELSE '5k+'
            END as bucket,
            COUNT(*) as cnt
        FROM notices GROUP BY bucket ORDER BY MIN(LENGTH(full_text))
    """).fetchall()
    for bucket, cnt in buckets:
        console.print(f"  {bucket:10s} {cnt:5d}")

    console.print(f"\n[bold]Communes sans notices :[/bold]")
    orphans = con.execute(
        "SELECT c.commune_id, c.commune_name FROM communes c "
        "WHERE NOT EXISTS (SELECT 1 FROM notices n WHERE n.commune_id = c.commune_id) "
        "ORDER BY c.commune_id LIMIT 20"
    ).fetchall()
    if orphans:
        for cid, name in orphans:
            console.print(f"  {cid} — {name}")
    else:
        console.print("  [green]Aucune[/green]")

    con.close()


if __name__ == "__main__":
    cli()
