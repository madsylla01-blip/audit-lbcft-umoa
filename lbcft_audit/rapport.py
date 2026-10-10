"""Génération du rapport de mission (Markdown) à partir des résultats et des constats 5C."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

from .constats import Constat, opinion, points_forts, rediger_constats
from .moteur import ResultatsAudit
from .outils import fcfa, nombre, pourcentage


def _tableau_md(table: pd.DataFrame) -> str:
    entete = "| " + " | ".join(str(c) for c in table.columns) + " |"
    separateur = "| " + " | ".join("---" for _ in table.columns) + " |"
    lignes = [
        "| " + " | ".join("" if pd.isna(v) else str(v).replace("|", "/") for v in ligne) + " |"
        for ligne in table.itertuples(index=False)
    ]
    return "\n".join([entete, separateur, *lignes])


def _constat_md(c: Constat) -> str:
    return f"""### {c.numero} — {c.titre}

**Notation : {c.notation}** · Tests : {", ".join(c.tests)} · Responsable proposé : {c.responsable} · Échéance proposée : {c.echeance}

| | |
|---|---|
| **Critère** | {c.critere} |
| **Constat** | {c.constat} |
| **Cause** | {c.cause} |
| **Conséquence** | {c.consequence} |
| **Recommandation** | {c.recommandation} |
| **Réponse de l'audité** | *À recueillir lors de la réunion de clôture.* |
"""


def generer_rapport(r: ResultatsAudit) -> str:
    p, d = r.parametres, r.donnees
    constats = rediger_constats(r)
    avis = opinion(constats)
    repartition = Counter(c.notation for c in constats)
    cou = r["COU-01"].annexes["couverture_par_test"].set_index("test").loc["Ensemble"]
    synthese = r.synthese()
    synthese_md = synthese.assign(
        population=synthese["population"].map(nombre),
        exceptions=synthese["exceptions"].map(nombre),
        montant_concerne=synthese["montant_concerne"].map(lambda m: fcfa(m, "M") if pd.notna(m) and m else "—"),
    )[["code", "test", "unite", "population", "exceptions", "montant_concerne"]]
    synthese_md.columns = ["Code", "Test", "Unité", "Population", "Exceptions", "Montant concerné"]
    plan = pd.DataFrame(
        [
            {
                "Constat": f"{c.numero} — {c.titre}",
                "Notation": c.notation,
                "Recommandation": c.recommandation,
                "Responsable": c.responsable,
                "Échéance": c.echeance,
            }
            for c in constats
        ]
    )
    fait_marquant = (
        f"**{pourcentage(cou.clients_identifies - cou.clients_avec_alerte, cou.clients_identifies)} des "
        f"{int(cou.clients_identifies)} clients présentant des schémas à risque n'ont déclenché aucune alerte** "
        "de l'outil de surveillance sur douze mois"
    )
    cles = "\n".join(f"- **{c.numero} ({c.notation})** — {c.titre}." for c in constats[:5])
    forts = "\n".join(f"- {x}" for x in points_forts(r))
    detail = "\n".join(_constat_md(c) for c in constats)
    nb_par_notation = ", ".join(
        f"{repartition[n]} {n.lower()}{'s' if repartition[n] > 1 else ''}"
        for n in ("Critique", "Majeur", "Modéré", "Faible")
        if repartition[n]
    )

    return f"""# Rapport de mission — Évaluation du dispositif LBC/FT

> **Projet de rapport généré automatiquement** par `python -m lbcft_audit rapport` à partir des données
> **100 % fictives** de la *{p.banque}*. Les faits chiffrés sont calculés ; les causes sont présumées et
> doivent être confirmées en entretien ; l'opinion et les recommandations relèvent du jugement de
> l'auditeur. Confidentiel — usage interne (sur données réelles).

| | |
|---|---|
| **Entité auditée** | {p.banque} — dispositif de lutte contre le blanchiment de capitaux et le financement du terrorisme |
| **Période testée** | du {p.periode_debut:%d/%m/%Y} au {p.periode_fin:%d/%m/%Y} (date d'arrêté : {p.date_arrete:%d/%m/%Y}) |
| **Populations** | {nombre(len(d.clients))} clients, {nombre(len(d.comptes))} comptes, {nombre(len(d.operations))} opérations, {nombre(len(d.alertes))} alertes, {len(d.declarations_soupcon)} déclarations de soupçon |
| **Approche** | {len(r.tests)} tests exhaustifs par analyse de données (100 % des populations), exceptions à qualifier sur pièces |
| **Date du projet** | {date.today():%d/%m/%Y} |

## 1. Synthèse

**Opinion proposée : {avis}** — à valider par le responsable de l'audit interne.

L'audit a évalué la capacité du dispositif à détecter, analyser et déclarer les opérations à risque. Il
relève **{len(constats)} constats** ({nb_par_notation}). Le fait marquant : {fait_marquant}.

Constats clés :

{cles}

![Couverture du dispositif](img/couverture_dispositif.png)

## 2. Contexte, périmètre et approche

- **Pourquoi cette mission.** L'Instruction BCEAO n°001-03-2025 prévoit que le dispositif de contrôle LBC/FT
  soit audité au moins une fois par an, les conclusions étant soumises à l'organe délibérant (art. 11).
- **Périmètre.** Surveillance des opérations, obligations déclaratives (DS, DTE), traitement des alertes,
  connaissance client (KYC, PPE, bénéficiaires effectifs) et filtrage des sanctions.
- **Approche.** Contrôles d'intégrité des extractions, puis réexécution indépendante de {len(r.tests)} tests
  sur 100 % des populations (voir `docs/06_catalogue_des_tests.md`). Les paramètres réglementaires
  sont sourcés ; les hypothèses d'audit sont signalées dans `config/parametres.yaml`.
- **Limites.** Les exceptions ne sont pas des constats tant qu'elles n'ont pas été vérifiées sur pièces.
  L'audit ne qualifie pas le soupçon : les cas sont transmis à la conformité, seule habilitée à
  déclarer à la CENTIF. Les totaux d'opérations restent à rapprocher de la comptabilité.

## 3. Points forts relevés

{forts}

## 4. Constats détaillés (format 5C)

{detail}
## 5. Plan d'action proposé

{_tableau_md(plan)}

## 6. Annexes

### 6.1 Résultats par test

{_tableau_md(synthese_md)}

### 6.2 Contrôles d'intégrité

{_tableau_md(r.integrite[["table", "controle", "resultat", "statut"]])}

### 6.3 Graphiques

![Clients concernés par test](img/clients_par_test.png)

![Fractionnement](img/fractionnement_exemple.png)

![Réseau de clients liés](img/reseau_exemple.png)

![Pays listés par le GAFI](img/pays_gafi.png)

![Ancienneté des alertes](img/alertes_anciennete.png)

![Délais des DS](img/delais_ds.png)

![KYC par agence](img/kyc_par_agence.png)
"""


def ecrire_rapport(r: ResultatsAudit, chemin: str | Path) -> Path:
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(generer_rapport(r), encoding="utf-8")
    return chemin


def generer_evaluation(r: ResultatsAudit, evaluation: pd.DataFrame, verite: pd.DataFrame) -> str:
    """Page « tester les tests » : rappel et précision de chaque scénario sur la vérité terrain."""
    table = evaluation.copy()
    for colonne in ("rappel", "precision"):
        table[colonne] = table[colonne].map(lambda x: "—" if pd.isna(x) else pourcentage(x, 1))
    table.columns = [
        "Test",
        "Typologie ciblée",
        "Cas injectés",
        "Cas détectés",
        "Rappel",
        "Clients signalés",
        "dont schémas suspects",
        "dont situations légitimes",
        "Précision",
    ]
    legitimes = verite[verite["typologie"] == "FAUX_POSITIF"]
    lignes_fp = []
    for code in evaluation["test"]:
        signales = r[code].clients
        for x in legitimes[legitimes["id_client"].isin(signales)].itertuples():
            lignes_fp.append(f"| {code} | {x.id_client} | {x.detail} |")
    faux_positifs = "\n".join(lignes_fp) or "| — | — | — |"
    return f"""# 8. Évaluation des tests (« tester les tests »)

> Page générée par `python -m lbcft_audit rapport`. Elle n'a de sens que sur des données synthétiques :
> sur des données réelles, la « vérité terrain » n'existe pas et la qualité des tests s'apprécie par la
> revue sur pièces d'un échantillon d'exceptions.

Le générateur de données injecte des schémas connus (fractionnement, comptes de passage, réseaux, etc.) et
des **situations atypiques mais légitimes**. On peut donc mesurer, pour chaque scénario de l'audit :

- le **rappel** : part des cas injectés effectivement détectés (un test qui rate des cas est dangereux) ;
- la **précision** : part des clients signalés relevant d'un schéma suspect injecté (un test trop bavard
  épuise les équipes et noie les vrais cas).

{_tableau_md(table)}

## Faux positifs : pourquoi la revue sur pièces reste indispensable

Les situations légitimes signalées par les tests, et l'explication qui permet de les lever :

| Test | Client | Explication (justificatif) |
|---|---|---|
{faux_positifs}

## Lecture

- Un rappel de 100 % sur un jeu synthétique ne garantit rien sur des données réelles : les typologies
  injectées sont celles que les tests cherchent. L'intérêt est ailleurs : vérifier que le code fait ce que
  la méthodologie annonce, et **calibrer les paramètres** en observant l'arbitrage rappel / précision.
- Les tests unitaires (`tests/`) vérifient ces résultats à chaque modification du code (intégration continue).
"""
