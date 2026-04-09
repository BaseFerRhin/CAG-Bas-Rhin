# Architecture — CAG Bas-Rhin 67/1

## Vue d'ensemble

L'application suit une architecture en pipeline linéaire avec 4 couches découplées :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLI (Click)                                   │
│  python -m src [extract | geocode | stats | eda | export]              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────────────┐  │
│  │   Extraction      │  │    Storage       │  │        UI            │  │
│  │  src/extraction/  │  │  src/storage/    │  │    src/ui/           │  │
│  │  6 fichiers       │→│  3 fichiers      │→│   12 fichiers        │  │
│  │  (~560 lignes)    │  │  (~460 lignes)   │  │   (~1200 lignes)    │  │
│  └──────────────────┘  └─────────────────┘  └───────────────────────┘  │
│                                                                         │
│  ┌──────────────────┐                                                   │
│  │   Export          │                                                   │
│  │  src/export/      │                                                   │
│  │  1 fichier        │                                                   │
│  └──────────────────┘                                                   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │   Configuration : config.yaml → AppConfig (dataclass)           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Pipeline d'extraction (4 phases)

Orchestré par `src/extraction/pipeline.py` → `run_extraction()`.

```
Phase 1: PDF → Pages         Phase 2: Pages → Communes
┌─────────────────────┐      ┌──────────────────────────┐
│  PDFReader           │      │  CommuneSplitter          │
│  pdfplumber          │──────│  regex _COMMUNE_RE        │
│  page_range 154–660  │      │  commune_id 3 chiffres    │
│  → list[PageText]    │      │  → list[CommuneNotice]    │
└─────────────────────┘      └──────────────────────────┘
                                         │
Phase 3: Communes → Sub-notices          │
┌──────────────────────────┐             │
│  NoticeParser             │◀────────────┘
│  4 regex: numérotation,   │
│  lieu-dit, biblio, figures │
│  → list[SubNotice]        │
└──────────────────────────┘
         │
Phase 4: Classification + Records
┌──────────────────────────────────────────────┐
│  IronAgeFilter              RecordBuilder     │
│  26 mots-clés Fer FR/DE    40 vestiges regex  │
│  21 périodes générales      9 types de sites   │
│  23 règles normalisation    3 niveaux confiance│
│  → is_fer, all_periods      → SiteRecord       │
└──────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────┐
  │  DuckDB loader    │
  │  6 tables INSERT   │
  │  DELETE + ré-insert│
  └──────────────────┘
```

### Phase 1 — Extraction texte (`pdf_reader.py`)

| Classe | `PDFReader` |
|---|---|
| Entrée | Chemin PDF, plage de pages (154–660) |
| Sortie | `list[PageText]` (page_num, text, commune_header, tables) |
| Outil | pdfplumber — extraction native (pas d'OCR) |
| Regex | `_COMMUNE_HEADER_RE` — détection en-tête commune |
| Particularité | Gestion layout 2 colonnes du PDF |

### Phase 2 — Découpage communal (`commune_splitter.py`)

| Classe | `CommuneSplitter` |
|---|---|
| Entrée | `list[PageText]` |
| Sortie | `list[CommuneNotice]` (commune_id, commune_name, text, page_start, page_end) |
| Regex | `_COMMUNE_RE` — pattern `NNN — Nom de commune` |
| Logique | Concaténation du texte, repérage des en-têtes, calcul des pages de début/fin |

### Phase 3 — Parsing des sous-notices (`notice_parser.py`)

| Classe | `NoticeParser` |
|---|---|
| Entrée | `CommuneNotice` |
| Sortie | `list[SubNotice]` |
| Regex (4) | `_NUMBERED_RE` (entrées numérotées), `_LIEU_DIT_RE` (lieux-dits), `_BIBLIO_RE` (bibliographie), `_FIG_REF_RE` (figures) |
| Champs extraits | entry_number, sous_notice_code, lieu_dit, text, bibliographie, figures_refs |

### Phase 4a — Filtre âge du Fer (`iron_age_filter.py`)

| Classe | `IronAgeFilter` |
|---|---|
| Rôle | Détection de l'âge du Fer, extraction et normalisation des périodes |
| Méthodes | `is_iron_age()`, `extract_iron_age_terms()`, `extract_all_periods()`, `normalize_period()`, `is_fer_norm()` |
| `_FER_KEYWORDS` | 26 alternants (FR + DE) : hallstatt, la tène, Ha [A-D], LT [A-D], protohistor, tumulus, eisenzeit, Grabhügel, Ringwall... |
| `_ALL_PERIODS` | 21 alternants couvrant toutes les périodes (néolithique → médiéval) |
| `_NORM_MAP` | 23 règles pattern→label : Ha A...Ha D3, LT A...LT D, BF III, Hallstatt, La Tène, Gallo-romain, etc. |
| `_FER_NORMS` | 15 labels normalisés appartenant à l'âge du Fer |

### Phase 4b — Construction des enregistrements (`record_builder.py`)

| Classe | `RecordBuilder` |
|---|---|
| Entrée | `SubNotice` + is_fer + all_periods |
| Sortie | `SiteRecord` (16 champs) |
| `_VESTIGES_RE` | 40 alternants (FR + DE) : tumulus, sépulture, fibule, céramique, Grabhügel... |
| `_guess_type()` | Hiérarchie de 9 types avec priorité : oppidum > sanctuaire > nécropole > tumulus > sépulture > habitat > atelier > dépôt > indéterminé |
| `_estimate_confidence()` | 3 niveaux (HIGH/MEDIUM/LOW) basés sur : fouille/sondage, références récentes (1980-2029), figures, nb refs biblio |
| Déduplication | Suffixe `_N` ajouté aux `notice_id` en cas de collision |

## Couche Storage

### Schéma (`schema.py`)

6 tables relationnelles + 5 vues analytiques. Voir [DATABASE.md](DATABASE.md) pour le détail complet.

### Chargement (`loader.py`)

Stratégie : **DELETE + ré-insert** (idempotent). Ordre de suppression respecte les FK (figures → bibliographie → vestiges → periodes → notices → communes), puis insertion dans l'ordre inverse.

7 fonctions : `load_records()` orchestre `_load_communes()`, `_load_notices()`, `_load_periodes()`, `_load_vestiges()`, `_load_bibliographie()`, `_load_figures()`.

### Requêtes (`queries.py`)

11 fonctions analytiques pré-définies + géocodage BAN. Voir [API.md](API.md) pour le catalogue complet.

## Couche UI (Dash)

### Factory (`app.py`)

`create_app()` construit l'application Dash avec :

- **Thème** : Bootstrap DARKLY + police Inter
- **Layout** : Navbar fixe + conteneur dynamique (`page-content`)
- **Navigation** : Callback manuel (pas de `use_pages=True`)
- **7 callbacks** enregistrés via `_register_callbacks(app)`

### Callbacks

| # | Déclencheur | Sorties | Fonction |
|---|---|---|---|
| 1 | Navigation (4 NavLink clicks) | page-content + 4 nav actifs | `navigate()` |
| 2 | Carte filtres (slider + switch) | carte-map figure | `update_map()` |
| 3 | Carte clic point | carte-detail-panel | `carte_detail()` |
| 4 | Notices recherche/filtre | notices-commune-list | `update_commune_list()` |
| 5 | Notices clic commune (pattern-matching ALL) | notices-detail | `show_notice_detail()` |
| 6 | Page courante | 3 figures chronologie | `update_chronology()` |
| 7 | Page courante | KPIs + 4 figures stats | `update_stats()` |

### Pages

| Page | Fichier `pages/` | Composants | Données |
|---|---|---|---|
| Carte | `carte.py` | `scatter_map`, Slider, Switch | `get_commune_stats()` |
| Notices | `notices.py` | ListGroup (pattern-matching), Cards | `get_all_notices()` |
| Chronologie | `chronologie.py` | 2 bar charts + 1 heatmap | SQL direct (periodes, co-occurrences) |
| Statistiques | `stats.py` | KPI cards, pie, bar, treemap | `get_summary_stats()`, `get_commune_stats()`, SQL vestiges/confiance |

### Composants réutilisables

| Composant | Fichier | Rôle |
|---|---|---|
| `create_commune_map()` | `commune_map.py` | Carte scatter_map avec taille proportionnelle |
| `render_notice_card()` | `notice_card.py` | Carte notice avec highlight regex des termes Fer |
| `create_period_bar()` | `period_chart.py` | Bar chart horizontal des périodes |
| `create_type_donut()` | `type_chart.py` | Donut des types de sites |

### Palettes de couleurs

**Types de sites** (9 couleurs) :

| Type | Couleur |
|---|---|
| nécropole | `#6A3D9A` |
| habitat | `#1F78B4` |
| oppidum | `#E31A1C` |
| tumulus | `#FB9A99` |
| sépulture | `#CAB2D6` |
| sanctuaire | `#33A02C` |
| dépôt | `#FF7F00` |
| atelier | `#B15928` |
| indéterminé | `#B2DF8A` |

**Périodes** (20 couleurs) : palette Hallstatt orangée → La Tène verte, avec variantes par sous-période.

## Configuration

Fichier `config.yaml` chargé via `src/config.py` → `AppConfig` (dataclass).

| Section | Clé | Défaut | Description |
|---|---|---|---|
| (racine) | `pdf_path` | `../../RawData/.../CAG Bas-Rhin.pdf` | Chemin vers le PDF source |
| `page_range` | `start`, `end` | 154, 660 | Plage de pages à extraire |
| (racine) | `source_label` | `cag_67` | Label source pour les IDs |
| (racine) | `department` | `67` | Code département |
| (racine) | `db_path` | `data/cag67.duckdb` | Chemin base DuckDB |
| `geocoding` | `provider` | `ban` | API de géocodage |
| `geocoding` | `cache_path` | `data/communes_geo.json` | Cache GeoJSON |
| `geocoding` | `throttle_rps` | `10` | Limite requêtes/seconde |
| `ui` | `port` | `8051` | Port du serveur Dash |
| `ui` | `debug` | `true` | Mode debug |
| (racine) | `log_level` | `INFO` | Niveau de log |

## Flux de données complet

```
                    PDF (735 pages)
                         │
                    ┌────┴────┐
                    │ Phase 1  │  PDFReader
                    │ 507 pages│  pdfplumber
                    └────┬────┘
                         │
                    ┌────┴────┐
                    │ Phase 2  │  CommuneSplitter
                    │ 551 comm.│  regex NNN—Nom
                    └────┬────┘
                         │
                    ┌────┴────┐
                    │ Phase 3  │  NoticeParser
                    │ 1095 not.│  sous-notices
                    └────┬────┘
                         │
              ┌──────────┴──────────┐
              │                      │
         ┌────┴────┐           ┌────┴────┐
         │ Phase 4a │           │ Phase 4b │
         │ IronAge  │           │ Records  │
         │ Filter   │           │ Builder  │
         │ 267 Fer  │           │ 9 types  │
         └────┬────┘           └────┬────┘
              │                      │
              └──────────┬──────────┘
                         │
                    ┌────┴────┐
                    │ DuckDB   │  6 tables
                    │ Loader   │  5 vues
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────┴────┐ ┌──┴───┐ ┌───┴────┐
         │ Geocode  │ │ Dash │ │ Export  │
         │ BAN API  │ │  UI  │ │  JSON   │
         │ 473 comm.│ │ :8051│ │        │
         └─────────┘ └──────┘ └────────┘
```
