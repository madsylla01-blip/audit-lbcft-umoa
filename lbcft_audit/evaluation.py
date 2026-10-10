"""Évaluation des tests d'audit sur la vérité terrain du jeu fictif (« tester les tests »).

La vérité terrain n'existe que parce que les données sont synthétiques. Elle permet de
mesurer, pour chaque scénario de l'audit :
- le rappel : part des cas injectés effectivement détectés ;
- la précision : part des clients signalés qui relèvent bien d'un schéma suspect injecté
  (les autres sont des situations légitimes, à lever lors de la revue sur pièces).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .donnees import lire_table
from .moteur import ResultatsAudit

CIBLES = {
    "OPE-01": "FRACTIONNEMENT",
    "OPE-02": "COMPTE_DE_PASSAGE",
    "OPE-03": "INCOHERENCE_PROFIL",
    "OPE-04": "REACTIVATION_DORMANT",
    "OPE-05": "PAYS_A_RISQUE",
    "OPE-06": "RESEAU",
    "FIL-01": "SANCTIONS_CORRESPONDANCE",
}


def charger_verite(dossier: str | Path) -> pd.DataFrame:
    return lire_table(Path(dossier) / "verite_terrain.csv", "verite_terrain")


def evaluer(resultats: ResultatsAudit, verite: pd.DataFrame) -> pd.DataFrame:
    suspects = set(verite.loc[verite["typologie"] != "FAUX_POSITIF", "id_client"])
    legitimes = set(verite.loc[verite["typologie"] == "FAUX_POSITIF", "id_client"])
    lignes = []
    for code, typologie in CIBLES.items():
        cible = set(verite.loc[verite["typologie"] == typologie, "id_client"])
        if code == "OPE-05":  # seuls les pays absents de la liste de la banque produisent des exceptions
            pays = verite.loc[verite["typologie"] == typologie].set_index("id_client")["detail"].str[-2:]
            cible = {c for c in cible if pays[c] not in resultats.parametres.pays_liste_banque}
        signales = resultats[code].clients
        if code == "FIL-01":
            ex = resultats[code].exceptions
            signales = set(ex.loc[ex["qualification"].str.startswith("Correspondance forte"), "id_client"])
        lignes.append(
            {
                "test": code,
                "typologie_cible": typologie,
                "cas_injectes": len(cible),
                "cas_detectes": len(signales & cible),
                "rappel": len(signales & cible) / len(cible) if cible else None,
                "clients_signales": len(signales),
                "dont_schemas_suspects": len(signales & suspects),
                "dont_situations_legitimes": len(signales & legitimes),
                "precision": len(signales & suspects) / len(signales) if signales else None,
            }
        )
    return pd.DataFrame(lignes)
