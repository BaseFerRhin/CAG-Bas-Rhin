# Base de données — DuckDB

## Vue d'ensemble

La base `data/cag67.duckdb` est une base analytique embarquée (DuckDB >= 1.1) contenant 6 tables relationnelles et 5 vues analytiques.

```
┌──────────────┐
│   communes   │──────┐
│  (PK: id)    │      │  1:N
└──────────────┘      │
                       ▼
                ┌──────────────┐
                │   notices    │──────┬──────┬──────┬──────┐
                │  (PK: id)    │      │      │      │      │
                └──────────────┘      │      │      │      │
                                      │ 1:N  │ 1:N  │ 1:N  │ 1:N
                                      ▼      ▼      ▼      ▼
                               ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
                               │periodes│ │vestiges│ │ biblio │ │figures │
                               └────────┘ └────────┘ └────────┘ └────────┘
```

## Tables

### `communes`

Table principale des communes du Bas-Rhin extraites du PDF.

| Colonne | Type | Contrainte | Description |
|---|---|---|---|
| `commune_id` | `VARCHAR` | `PRIMARY KEY` | Code à 3 chiffres (ex: `001`, `551`) |
| `commune_name` | `VARCHAR` | `NOT NULL` | Nom de la commune |
| `page_start` | `INTEGER` | | Première page dans le PDF |
| `page_end` | `INTEGER` | | Dernière page dans le PDF |
| `latitude` | `DOUBLE` | | Latitude WGS84 (remplie par géocodage) |
| `longitude` | `DOUBLE` | | Longitude WGS84 |
| `x_l93` | `DOUBLE` | | Coordonnée X Lambert-93 |
| `y_l93` | `DOUBLE` | | Coordonnée Y Lambert-93 |

### `notices`

Sous-notices archéologiques, une par site ou découverte.

| Colonne | Type | Contrainte | Description |
|---|---|---|---|
| `notice_id` | `VARCHAR` | `PRIMARY KEY` | Format `CAG67-{commune_id}[-{code}][_N]` |
| `commune_id` | `VARCHAR` | `NOT NULL`, `FK → communes` | Référence vers la commune |
| `sous_notice_code` | `VARCHAR` | | Code de sous-notice (ex: `006`, `013`) |
| `lieu_dit` | `VARCHAR` | | Lieu-dit mentionné |
| `type_site` | `VARCHAR` | | Type classifié (9 valeurs possibles) |
| `raw_text` | `VARCHAR` | | Texte tronqué à 500 caractères |
| `full_text` | `VARCHAR` | | Texte intégral de la notice |
| `page_number` | `INTEGER` | | Page dans le PDF |
| `has_iron_age` | `BOOLEAN` | `DEFAULT false` | Contient des mentions âge du Fer |
| `confidence_level` | `VARCHAR` | `DEFAULT 'LOW'` | Niveau de confiance : `HIGH`, `MEDIUM`, `LOW` |

**Valeurs de `type_site`** : `oppidum`, `sanctuaire`, `nécropole`, `tumulus`, `sépulture`, `habitat`, `atelier`, `dépôt`, `indéterminé`

### `periodes`

Mentions chronologiques extraites de chaque notice (N:1 vers notices).

| Colonne | Type | Contrainte | Description |
|---|---|---|---|
| `notice_id` | `VARCHAR` | `NOT NULL`, `FK → notices` | Référence vers la notice |
| `periode` | `VARCHAR` | `NOT NULL` | Mention brute extraite du texte |
| `periode_norm` | `VARCHAR` | | Label normalisé (23 valeurs possibles) |
| `is_iron_age` | `BOOLEAN` | `DEFAULT false` | Période appartenant à l'âge du Fer |

### `vestiges`

Vestiges et mobilier archéologique détectés par notice (N:1 vers notices).

| Colonne | Type | Contrainte | Description |
|---|---|---|---|
| `notice_id` | `VARCHAR` | `NOT NULL`, `FK → notices` | Référence vers la notice |
| `vestige` | `VARCHAR` | `NOT NULL` | Type de vestige détecté (40 termes possibles) |

### `bibliographie`

Références bibliographiques extraites des notices (N:1 vers notices).

| Colonne | Type | Contrainte | Description |
|---|---|---|---|
| `notice_id` | `VARCHAR` | `NOT NULL`, `FK → notices` | Référence vers la notice |
| `reference` | `VARCHAR` | `NOT NULL` | Référence bibliographique brute |

### `figures`

Références aux figures du PDF (N:1 vers notices).

| Colonne | Type | Contrainte | Description |
|---|---|---|---|
| `notice_id` | `VARCHAR` | `NOT NULL`, `FK → notices` | Référence vers la notice |
| `figure_ref` | `VARCHAR` | `NOT NULL` | Référence à la figure (ex: `fig. 123`) |
| `page_number` | `INTEGER` | | Page de la notice contenant la référence |

## Vues analytiques

### `v_fer_notices`

Notices de l'âge du Fer avec coordonnées géographiques.

```sql
SELECT n.*, c.commune_name AS commune, c.latitude, c.longitude
FROM notices n
JOIN communes c ON n.commune_id = c.commune_id
WHERE n.has_iron_age = true
```

### `v_stats_by_commune`

Agrégation par commune : nombre total de notices, notices Fer, diversité des types.

```sql
SELECT c.commune_id, c.commune_name, c.latitude, c.longitude,
       COUNT(*) AS total_notices,
       COUNT(*) FILTER (WHERE n.has_iron_age) AS fer_notices,
       COUNT(DISTINCT n.type_site) AS type_count
FROM communes c
LEFT JOIN notices n ON c.commune_id = n.commune_id
GROUP BY c.commune_id, c.commune_name, c.latitude, c.longitude
```

### `v_stats_by_type`

Ventilation par type de site, avec décompte global et Fer.

```sql
SELECT type_site, COUNT(*) AS count,
       COUNT(*) FILTER (WHERE has_iron_age) AS fer_count
FROM notices
GROUP BY type_site
ORDER BY count DESC
```

### `v_stats_by_periode`

Ventilation par période (brute et normalisée).

```sql
SELECT p.periode, p.periode_norm, p.is_iron_age,
       COUNT(DISTINCT p.notice_id) AS notice_count
FROM periodes p
GROUP BY p.periode, p.periode_norm, p.is_iron_age
ORDER BY notice_count DESC
```

### `v_period_cooccurrence`

Co-occurrences de périodes normalisées sur les mêmes notices (matrice triangulaire supérieure).

```sql
SELECT a.periode_norm AS period_a, b.periode_norm AS period_b,
       COUNT(DISTINCT a.notice_id) AS co_count
FROM periodes a
JOIN periodes b ON a.notice_id = b.notice_id
  AND a.periode_norm < b.periode_norm
WHERE a.periode_norm IS NOT NULL AND b.periode_norm IS NOT NULL
GROUP BY a.periode_norm, b.periode_norm
ORDER BY co_count DESC
```

## Stratégie de chargement

Le `loader.py` utilise une approche **DELETE + ré-insert** pour garantir l'idempotence :

1. Suppression dans l'ordre : `figures` → `bibliographie` → `vestiges` → `periodes` → `notices` → `communes`
2. Insertion dans l'ordre inverse : `communes` → `notices` → `periodes` → `vestiges` → `bibliographie` → `figures`

La déduplication des communes est gérée par un `set()` de `commune_id` déjà vus lors de l'insertion.

## Géocodage

Le géocodage est incrémental (`WHERE latitude IS NULL`) et enrichit la table `communes` avec :
- `latitude` / `longitude` (WGS84)
- `x_l93` / `y_l93` (Lambert-93 via pyproj)

Le cache est stocké en GeoJSON (`data/communes_geo.json`) pour éviter les appels répétés à l'API BAN.

## Volumétrie typique

| Table | Lignes |
|---|---|
| `communes` | 551 |
| `notices` | 1 095 |
| `periodes` | ~2 500 |
| `vestiges` | ~3 000 |
| `bibliographie` | ~1 500 |
| `figures` | 550 |
