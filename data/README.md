# Données — dictionnaire

> **Toutes les données de ce dossier sont fictives.** Elles sont générées par
> `python -m lbcft_audit generer` (graine fixe : le résultat est identique à chaque exécution).
> Toute ressemblance avec des personnes ou des entités existantes serait fortuite.
> **Ne jamais déposer de données réelles dans ce dépôt.**

Format commun : CSV, séparateur « ; », encodage UTF-8 avec BOM (lisible directement dans Excel), dates
`AAAA-MM-JJ` ou `AAAA-MM-JJ hh:mm:ss`, montants en FCFA.

## `synthetiques/clients.csv` — 1 ligne par client

| Colonne | Description |
|---|---|
| `id_client` | Identifiant interne (CL00001…) |
| `type_client` | `PP` personne physique, `PM` personne morale |
| `nom_complet` | Nom et prénom (PP) ou raison sociale (PM) |
| `date_naissance` / `date_creation` | Date de naissance (PP) / de création (PM) |
| `nationalite` | Code pays ISO à 2 lettres (PP) |
| `profession` / `secteur_activite` | Profession (PP) / secteur d'activité (PM) |
| `revenu_mensuel_declare` / `chiffre_affaires_annuel_declare` | Profil financier déclaré à l'entrée en relation |
| `telephone`, `adresse` | Coordonnées (utilisées pour détecter les identifiants partagés) |
| `agence` | Agence de rattachement (AG01 à AG06) |
| `date_entree_relation` | Date d'entrée en relation |
| `niveau_risque` | Classification attribuée par la banque : `FAIBLE`, `MOYEN`, `ELEVE` |
| `ppe`, `ppe_approbation_direction` | Personne politiquement exposée ; approbation de la haute direction (`OUI`/`NON`/vide) |
| `piece_type`, `piece_numero`, `piece_date_expiration` | Pièce d'identité (CNI, passeport, carte consulaire) ou RCCM |
| `beneficiaire_effectif_identifie` | PM : bénéficiaire effectif identifié (`OUI`/`NON`) |
| `date_derniere_revue_kyc` | Date de la dernière revue périodique du dossier |
| `date_dernier_filtrage`, `resultat_dernier_filtrage` | Dernier passage dans l'outil de filtrage des sanctions et son résultat |

## `synthetiques/comptes.csv` — 1 ligne par compte

`id_compte`, `id_client`, `type_compte` (COURANT, EPARGNE), `devise`, `agence`, `date_ouverture`,
`date_dernier_mouvement_avant_periode` (dernier mouvement avant le 01/07/2025, sert à repérer les comptes
inactifs), `statut` (ACTIF / INACTIF à la date d'arrêté).

## `synthetiques/operations.csv` — 1 ligne par opération (01/07/2025 – 30/06/2026)

| Colonne | Description |
|---|---|
| `id_operation`, `date_operation` | Identifiant et horodatage |
| `id_compte`, `id_client` | Compte mouvementé et son titulaire |
| `type_operation` | `VERSEMENT_ESPECES`, `RETRAIT_ESPECES`, `VIREMENT_RECU`, `VIREMENT_EMIS`, `TRANSFERT_INT_RECU`, `TRANSFERT_INT_EMIS` |
| `sens` | `C` crédit, `D` débit |
| `montant` | Montant en FCFA |
| `canal` | `GUICHET`, `GAB`, `BANQUE_DIGITALE`, `VIREMENT`, `SWIFT` |
| `agence_operation` | Agence où l'opération a été réalisée |
| `pays_contrepartie` | Pays de la contrepartie (transferts internationaux) |
| `contrepartie`, `libelle` | Nom de la contrepartie (fictif) et libellé |

## `synthetiques/alertes.csv` — alertes produites par l'outil de surveillance de la banque

`id_alerte`, `id_client`, `id_operation` (vide pour les alertes mensuelles), `scenario` (ESP-01, PAY-01,
PRO-01, TRF-01 : voir `config/parametres.yaml`), `date_alerte`, `analyste`, `statut` (OUVERTE / CLOTUREE),
`date_cloture`, `motif_cloture`, `decision` (EN_COURS, CLASSEMENT_SANS_SUITE, DECLARATION_SOUPCON).

## `synthetiques/declarations_soupcon.csv` — registre des déclarations de soupçon

`id_ds`, `id_alerte`, `id_client`, `date_alerte`, `date_decision` (décision de déclarer),
`date_transmission` (envoi à la CENTIF), `statut`.

## `synthetiques/declarations_especes.csv` — registre des déclarations de transactions en espèces

`id_dte`, `id_client`, `date_operation`, `type_operation`, `montant_declare`, `date_declaration`.

## `synthetiques/liste_sanctions.csv` — liste de sanctions **FICTIVE**

`id_entree` (FICT-001…), `nom`, `type_entite` (PP/PM), `date_naissance`, `programme`, `date_inscription`.
Cette liste n'a aucun lien avec une liste officielle.

## Fichiers d'évaluation (à ne pas utiliser dans les tests d'audit)

- `verite_terrain.csv` : clients sur lesquels une typologie a été injectée (ou une situation légitime
  atypique : `FAUX_POSITIF`).
- `metadonnees_generation.json` : anomalies de processus injectées (pièces expirées, alertes en
  souffrance, DTE manquantes…).

Ils servent uniquement à mesurer la performance des tests (`docs/08_evaluation_des_tests.md`) et aux tests
automatisés (`tests/`).
