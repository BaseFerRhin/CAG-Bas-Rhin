# API — CLI et requêtes analytiques

## CLI (`python -m src`)

Le point d'entrée CLI est `src/__main__.py`, construit avec Click.

### Commandes

#### `extract` — Extraction PDF → DuckDB

```bash
python -m src extract --pdf <chemin_pdf> [--config config.yaml]
```

| Option | Type | Requis | Description |
|---|---|---|---|
| `--pdf` | Path (existant) | Oui | Chemin vers le PDF CAG 67/1 |
| `--config` | Path | Non | Fichier de configuration (défaut: `config.yaml`) |

Exécute les 4 phases du pipeline et produit `data/cag67.duckdb`. Affiche un résumé avec métriques de qualité.

#### `geocode` — Géocodage des communes

```bash
python -m src geocode [--config config.yaml]
```

Enrichit la table `communes` avec les coordonnées WGS84 et Lambert-93 via l'API BAN. Utilise le cache GeoJSON configuré.

#### `export` — Export JSON

```bash
python -m src export --format raw-records --output <chemin> [--all] [--config config.yaml]
```

| Option | Type | Requis | Description |
|---|---|---|---|
| `--format` | Choice | Non | Format d'export (seul `raw-records` disponible) |
| `--output`, `-o` | Path | Oui | Fichier de sortie |
| `--all` | Flag | Non | Toutes les notices (pas seulement Fer) |

#### `stats` — Statistiques de la base

```bash
python -m src stats [--config config.yaml]
```

Affiche un tableau résumé : communes, notices, notices Fer, figures, géocodées, distribution par type et par période.

#### `eda` — EDA post-extraction

```bash
python -m src eda [--config config.yaml]
```

Analyse exploratoire détaillée :
- Métriques d'extraction (couverture, longueur moyenne/médiane)
- Top 10 communes par nombre de notices
- Distribution des longueurs de texte par buckets
- Communes sans notices (orphelines)

### UI Dash

```bash
python -m src.ui
# → http://localhost:8051
```

Lance le serveur Dash sur le port configuré (`config.yaml` → `ui.port`).

## Requêtes analytiques (`src/storage/queries.py`)

11 fonctions publiques pour interroger la base DuckDB. Toutes prennent `db_path: Path` en premier argument.

### Résumé

#### `get_summary_stats(db_path) → dict`

Retourne un dictionnaire avec :

| Clé | Type | Description |
|---|---|---|
| `communes` | int | Nombre total de communes |
| `notices` | int | Nombre total de notices |
| `fer_notices` | int | Nombre de notices âge du Fer |
| `geocoded` | int | Communes avec coordonnées |
| `figures` | int | Nombre de figures |
| `by_type` | list[tuple] | Distribution `(type_site, count)` pour les notices Fer |
| `by_periode` | list[tuple] | Distribution `(periode_norm, count)` pour les notices Fer |

#### `extraction_metrics(db_path) → dict`

Métriques de qualité de l'extraction :

| Clé | Type | Description |
|---|---|---|
| `total_communes` | int | Communes extraites |
| `total_notices` | int | Notices extraites |
| `iron_age_notices` | int | Notices Fer |
| `avg_notice_length` | int | Longueur moyenne du texte |
| `median_notice_length` | int | Longueur médiane |
| `communes_without_notices` | int | Communes orphelines |
| `coverage_rate` | float | % de communes avec au moins une notice |

### Notices

#### `get_fer_notices(db_path) → list[dict]`

Toutes les notices Fer avec coordonnées communes (via `v_fer_notices`), triées par `commune_id`.

#### `get_all_notices(db_path, *, iron_age_only=False) → list[dict]`

Toutes les notices (ou Fer uniquement), jointes avec les communes pour nom et coordonnées. Triées par `commune_id`, `sous_notice_code`.

#### `search_notices(db_path, query, *, iron_age_only=False) → list[dict]`

Recherche plein texte dans `full_text` avec logique AND sur les termes séparés par espaces. Utilise `ILIKE` (insensible à la casse). Limité à 200 résultats.

### Communes

#### `get_commune_stats(db_path) → list[dict]`

Statistiques par commune depuis `v_stats_by_commune`, triées par `fer_notices` DESC.

Colonnes retournées : `commune_id`, `commune_name`, `latitude`, `longitude`, `total_notices`, `fer_notices`, `type_count`.

#### `top_communes(db_path, *, limit=20, iron_age_only=True) → list[dict]`

Top N communes par nombre de notices (Fer ou total).

### Périodes

#### `period_distribution(db_path, *, normalized=True) → list[dict]`

Distribution des périodes, normalisées ou brutes. Retourne `periode`, `is_iron_age`, `cnt`.

#### `period_cooccurrence(db_path) → list[tuple[str, str, int]]`

Co-occurrences de périodes normalisées (via `v_period_cooccurrence`). Retourne des triplets `(period_a, period_b, co_count)`.

### Vestiges

#### `vestige_frequency(db_path, *, iron_age_only=True, limit=30) → list[dict]`

Fréquence des vestiges, optionnellement filtré sur les notices Fer. Retourne `vestige`, `cnt`.

### Géocodage

#### `geocode_communes(db_path, *, cache_path=None, throttle_rps=10) → int`

Géocode les communes sans coordonnées via l'API BAN.

**Processus** :
1. Charge le cache GeoJSON (format FeatureCollection)
2. Sélectionne les communes avec `latitude IS NULL`
3. Pour chaque commune : cache-hit ou appel BAN
4. Nettoyage du nom (`_clean_commune_name`) : suppression parenthèses, mentions « en allemand », etc.
5. Requête BAN : `q={nom} Bas-Rhin`, `type=municipality`, `limit=1`
6. Validation : contexte doit contenir « 67 » ou « Bas-Rhin »
7. Reprojection WGS84 → Lambert-93 (EPSG:2154) via pyproj
8. UPDATE en base + sauvegarde du cache

**Retour** : nombre de communes géocodées avec succès.

## Module Export (`src/export/to_raw_records.py`)

#### `export_raw_records(db_path, output, *, iron_age_only=True) → int`

Exporte les notices depuis DuckDB vers un fichier JSON, au format attendu par le pipeline parent BaseFerRhin. Retourne le nombre d'enregistrements exportés.

## Configuration (`src/config.py`)

4 dataclasses imbriquées :

```
AppConfig
├── pdf_path: str
├── page_range: PageRange
│   ├── start: int (154)
│   └── end: int (660)
├── source_label: str ("cag_67")
├── department: str ("67")
├── db_path: str ("data/cag67.duckdb")
├── geocoding: GeocodingConfig
│   ├── provider: str ("ban")
│   ├── cache_path: str ("data/communes_geo.json")
│   └── throttle_rps: int (10)
├── ui: UIConfig
│   ├── port: int (8051)
│   └── debug: bool (true)
└── log_level: str ("INFO")
```

Chargement via `load_config(path)` qui lit le YAML et instancie les dataclasses.

## Tests

45 tests répartis sur 6 modules, exécutables via `pytest` :

| Module | Tests | Couverture |
|---|---|---|
| `test_pdf_reader.py` | 6 | Dataclass PageText, détection en-tête commune, fixture pages |
| `test_commune_splitter.py` | 6 | Split communes, IDs 3 chiffres, noms nettoyés, plages de pages |
| `test_notice_parser.py` | 6 | Sous-notices numérotées, lieux-dits, bibliographie, figures |
| `test_iron_age_filter.py` | 11 | Hallstatt, La Tène, sous-périodes Ha/LT, termes DE, BF, exclusions, normalisation |
| `test_record_builder.py` | 10 | Construction basique, classification (tumulus/nécropole/sanctuaire/oppidum/habitat/indéterminé), troncature, confiance |
| `test_duckdb_storage.py` | 6 | Création schéma, idempotence, chargement, vues, métriques, rechargement |
