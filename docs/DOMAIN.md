# Domaine — Archéologie protohistorique du Bas-Rhin

## Contexte

La **Carte Archéologique de la Gaule 67/1** (CAG) est un inventaire systématique des sites archéologiques du département du Bas-Rhin. Rédigée par Pascal Flotté et Matthieu Fuchs, elle couvre toutes les périodes, de la Préhistoire au Moyen Âge.

Ce projet se concentre sur l'**âge du Fer** (env. 800 – 50 av. J.-C.), divisé en deux grandes phases :

| Période | Chronologie | Sous-périodes |
|---|---|---|
| **Hallstatt** (premier âge du Fer) | env. -800 à -450 | Ha A, Ha B, Ha C, Ha D (D1, D2, D3) |
| **La Tène** (second âge du Fer) | env. -450 à -50 | LT A, LT B, LT C, LT D |
| **Bronze Final** (transition) | env. -1000 à -800 | BF III (BF IIIa, BF IIIb) |

Le Bas-Rhin est une zone clé pour la protohistoire européenne, à la charnière entre les mondes celtique occidental et la sphère culturelle germanique/rhénane.

## Vocabulaire contrôlé

### Périodes normalisées (23 labels)

L'`IronAgeFilter` normalise les mentions brutes extraites du PDF vers un vocabulaire contrôlé de 23 labels.

**Sous-périodes Fer** (15 labels reconnus comme « âge du Fer ») :

| Label | Exemples de texte source |
|---|---|
| `Ha A` | « Ha A », « HaA2 » |
| `Ha B` | « Ha B », « HaB1 » |
| `Ha C` | « Ha C », « HaC » |
| `Ha D` | « Ha D » (sans chiffre) |
| `Ha D1` | « Ha D1 », « HaD1 » |
| `Ha D2` | « Ha D2 » |
| `Ha D3` | « Ha D3 » |
| `LT A` | « LT A », « La Tène A » |
| `LT B` | « LT B », « LTB » |
| `LT C` | « LT C » |
| `LT D` | « LT D », « LT finale », « La Tène finale » |
| `BF III` | « BF III », « BF IIIa », « âge du bronze final » |
| `Hallstatt` | « hallstatt », « hallstattien », « eisenzeit », « premier âge du fer » |
| `La Tène` | « la tène », « latènien », « latènezeit », « second âge du fer » |
| `Âge du Fer` | « âge du fer », « protohistorique » |

**Autres périodes** (8 labels) :

| Label | Correspondances |
|---|---|
| `Gallo-romain` | « gallo-romain », « gallo romain », « romain » |
| `Néolithique` | « néolithique » |
| `Mésolithique` | « mésolithique » |
| `Paléolithique` | « paléolithique » |
| `Âge du Bronze` | « âge du bronze » (hors « bronze final ») |
| `Mérovingien` | « mérovingien » |
| `Carolingien` | « carolingien » |
| `Médiéval` | « médiéval », « moyen âge » |

### Mots-clés de détection (bilingues FR/DE)

Le filtre intègre 26 mots-clés pour détecter les notices liées à l'âge du Fer, incluant des termes germaniques fréquents dans les publications alsaciennes et badoises :

| Français | Allemand |
|---|---|
| hallstatt, la tène, âge du fer | eisenzeit, latènezeit |
| tumulus, tertre funéraire | Grabhügel, Hügelgrab |
| — | Flachgrab (tombe plate) |
| — | Ringwall (enceinte circulaire) |
| — | Viereckschanze (enclos quadrangulaire) |
| — | Fürstengrab (tombe princière) |
| — | Fürstensitz (résidence princière) |
| protohistorique, hallstattien(ne), latènien(ne) | — |
| premier/second âge du fer, époque de hallstatt | — |
| BF IIIa/b, LT finale | — |

### Types de sites (9 catégories)

Le `RecordBuilder._guess_type()` classe chaque notice selon une hiérarchie de priorité basée sur les vestiges détectés :

| Priorité | Type | Vestiges déclencheurs |
|---|---|---|
| 1 | `oppidum` | oppidum, fortification, enceinte, ringwall, fürstensitz |
| 2 | `sanctuaire` | sanctuaire, fanum, lieu de culte, viereckschanze |
| 3 | `nécropole` | nécropole |
| 4 | `tumulus` | tumulus, tertre, grabhügel, hügelgrab, fürstengrab |
| 5 | `sépulture` | tombe, sépulture, inhumation, incinération, urne, brandgrab, flachgrab |
| 6 | `habitat` | habitat, silo, fosse, four, siedlung |
| 7 | `atelier` | atelier |
| 8 | `dépôt` | dépôt |
| 9 | `indéterminé` | (aucun vestige reconnu) |

La séparation tumulus/nécropole distingue les tertres funéraires individuels (hallstattiens) des ensembles funéraires structurés.

### Vestiges détectés (40 termes)

Le `_VESTIGES_RE` reconnaît 40 types de vestiges et mobilier :

**Structures** : tumulus, tertre, sépulture, nécropole, habitat, oppidum, fortification, enceinte, silo, fosse, four, atelier, dépôt, tombe, inhumation, incinération, sanctuaire, fanum, lieu de culte

**Mobilier** : urne, céramique, tesson(s), fibule, bracelet, épée, monnaie, torque, hache, rasoir, poignard, anneau, poterie

**Termes germaniques** : Viereckschanze, Grabhügel, Hügelgrab, Flachgrab, Ringwall, Siedlung, Brandgrab, Fürstengrab

## Niveau de confiance

Chaque notice reçoit un niveau de confiance (HIGH / MEDIUM / LOW) basé sur des heuristiques :

| Niveau | Critères |
|---|---|
| **HIGH** | Mention de fouille/sondage/prospection ET références bibliographiques récentes (1980-2029) |
| **MEDIUM** | Références récentes OU figures OU 3+ références bibliographiques |
| **LOW** | Aucun des critères ci-dessus |

Les mentions de fouille incluent les termes : « fouille », « sondage », « prospection systématique », « Grabung » (DE).

## Géocodage

Les communes sont géocodées via l'**API BAN** (Base Adresse Nationale) :

1. **Nettoyage** : suppression des parenthèses, mentions « en allemand », « antérieurement »
2. **Requête** : `q={commune} Bas-Rhin`, `type=municipality`
3. **Validation** : vérification que le contexte retourné contient « 67 » ou « Bas-Rhin »
4. **Reprojection** : WGS84 (lat/lon) → Lambert-93 (x_l93/y_l93) via pyproj
5. **Cache** : sauvegardé en GeoJSON (`data/communes_geo.json`)

Résultats : 473 communes géocodées sur 551 (85,8 %).

## Particularités du PDF source

Le PDF de la CAG Bas-Rhin présente plusieurs défis pour l'extraction automatique :

- **Layout 2 colonnes** : le texte des notices est disposé sur 2 colonnes par page
- **Structure semi-structurée** : les en-têtes de communes suivent le format `NNN — Nom` mais le corps est en texte libre
- **Multilinguisme** : mélange de français et d'allemand pour les toponymes et termes archéologiques
- **Références croisées** : figures référencées dans le texte (`fig. X`) renvoyant à des pages différentes
- **Variations typographiques** : « Ha C » vs « HaC » vs « Hallstatt C » pour la même sous-période

## Contexte géographique

Le Bas-Rhin couvre la plaine d'Alsace nord et les contreforts vosgiens, une zone de contact entre :

- Le **monde celtique** occidental (culture de Hallstatt/La Tène)
- La **sphère rhénane** (influences culturelles de la rive droite du Rhin)
- Les **Vosges du Nord** (sites de hauteur, oppida)

Les sites les plus remarquables incluent des tumulus hallstattiens de la plaine rhénane, des oppida sur les éperons vosgiens, et des nécropoles à incinération de La Tène.
