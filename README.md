# CAG Bas-Rhin (67/1)

Extraction et visualisation interactive de la **Carte Archéologique de la Gaule — Le Bas-Rhin** (P. Flotté, M. Fuchs).

Pipeline d'extraction PDF → DuckDB avec interface web Dash pour explorer les ~998 notices communales et les **~300–600 sites de l'âge du Fer** (Hallstatt / La Tène).

## Aperçu

```
CAG Bas-Rhin.pdf (735 pages, 209 Mo)
        │
        ▼
  ┌──────────────┐     ┌──────────┐     ┌──────────────┐
  │  Extraction   │────▶│  DuckDB  │────▶│   Dash UI    │
  │  pdfplumber   │     │  6 tables │     │  4 pages     │
  │  4 phases     │     │  4 vues   │     │  carte, etc. │
  └──────────────┘     └──────────┘     └──────────────┘
                              │
                              ▼
                    Export → Pipeline BaseFerRhin
```

### Périmètre

| Propriété | Valeur |
|---|---|
| Source | CAG 67/1 — Le Bas-Rhin |
| Auteurs | Pascal Flotté, Matthieu Fuchs |
| Pages PDF | 735 (507 pages de notices, p.154–660) |
| Communes | ~998 (numéros 001–999) |
| Département | Bas-Rhin (67) |
| Mentions Hallstatt | 645 |
| Mentions La Tène | 376 |
| Mentions tumulus | 382 |

## Installation

```bash
pip install -e ".[ui,dev]"
```

Prérequis système : aucun (le PDF est natif, pas besoin de Tesseract).

## Utilisation

### 1. Extraction (PDF → DuckDB)

```bash
python -m src extract --pdf "../../RawData/GrosFichiers - Béhague/CAG Bas-Rhin.pdf"
```

Produit `data/cag67.duckdb` avec 6 tables et 4 vues analytiques. Temps : ~90 secondes.

### 2. Géocodage des communes

```bash
python -m src geocode
```

Ajoute les centroïdes lat/lon (API BAN) à la table `communes`. Temps : ~30 secondes.

### 3. Interface web

```bash
python -m src.ui
# → http://localhost:8051
```

4 pages interactives :

| Page | Contenu |
|---|---|
| **Carte** | Communes sur carte, taille = nb notices Fer, filtres type/période |
| **Notices** | Navigateur de texte, recherche, highlight mots-clés, tags |
| **Chronologie** | Frise toutes périodes, zoom Fer, heatmap co-occurrences |
| **Statistiques** | KPIs, donut types, top communes, treemap vestiges, confiance |

### 4. Statistiques et EDA

```bash
python -m src stats                  # KPIs et distributions
python -m src eda                    # EDA détaillé (outliers, distributions)
```

### 5. Export vers BaseFerRhin

```bash
python -m src export --format raw-records --output ../../data/sources/cag67_records.json
python -m src export --all -o export/all_records.json   # toutes les notices
```

## Architecture

```
src/
├── extraction/          6 fichiers — PDF → notices → records
│   ├── pdf_reader.py        Phase 1 : pdfplumber page extraction (2 colonnes)
│   ├── commune_splitter.py  Phase 2 : split en notices communales
│   ├── notice_parser.py     Phase 3 : sous-notices et lieux-dits
│   ├── iron_age_filter.py   Phase 4 : filtre âge du Fer
│   ├── record_builder.py    Phase 4 : construction SiteRecord
│   └── pipeline.py          Orchestrateur des 4 phases
├── storage/             3 fichiers — DuckDB persistence
│   ├── schema.py            Création tables/vues
│   ├── loader.py            Insert records → DuckDB
│   └── queries.py           Requêtes analytiques pré-définies
├── export/              1 fichier — Export pipeline parent
│   └── to_raw_records.py    Conversion → RawRecord BaseFerRhin
└── ui/                  ~12 fichiers — Interface Dash multi-pages
    ├── app.py               Factory Dash (DARKLY theme)
    ├── layout.py            Layout principal + navigation
    ├── callbacks.py         Callbacks cross-page
    ├── pages/               4 pages (carte, notices, chronologie, stats)
    └── components/          4 composants (notice_card, commune_map, charts)
```

## Base DuckDB

6 tables + 4 vues :

| Table | Contenu |
|---|---|
| `communes` | 998 communes avec centroïdes géocodés |
| `notices` | Toutes les sous-notices (texte, type, page, Fer/non-Fer) |
| `periodes` | Mentions chronologiques par notice (brut + normalisé) |
| `vestiges` | Vestiges détectés par notice |
| `bibliographie` | Références bibliographiques |
| `figures` | Références aux figures du PDF |

| Vue | Usage |
|---|---|
| `v_fer_notices` | Notices âge du Fer avec coords communes |
| `v_stats_by_commune` | Agrégation par commune (total, Fer, types) |
| `v_stats_by_type` | Ventilation par type de site |
| `v_stats_by_periode` | Ventilation par période |
| `v_period_cooccurrence` | Co-occurrences de périodes par notice |

## Tests

```bash
pytest
```

| Module | Couverture |
|---|---|
| `test_pdf_reader.py` | Extraction texte, 2 colonnes, tables |
| `test_commune_splitter.py` | Split communes, multi-pages |
| `test_notice_parser.py` | Sous-notices, lieux-dits |
| `test_iron_age_filter.py` | Filtre Fer, exclusions |
| `test_record_builder.py` | Construction, classification |
| `test_duckdb_storage.py` | Schéma, insert, vues |

## Stack

- **Python** >= 3.11
- **pdfplumber** >= 0.11 — extraction texte PDF natif
- **DuckDB** >= 1.1 — base analytique embarquée
- **Dash** >= 2.14 + **dash-bootstrap-components** — UI web
- **Plotly** — cartes Scattermapbox, charts
- **pyproj** >= 3.6 — reprojection WGS84 ↔ Lambert-93
- **httpx** — géocodage API BAN

## Licence

MIT
