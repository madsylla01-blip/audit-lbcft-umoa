"""Contrôles d'intégrité des données extraites, à réaliser AVANT tout test d'audit.

Sans ces contrôles (et sans rapprochement des totaux avec la comptabilité), les
résultats des tests doivent être présentés comme provisoires.
"""

from __future__ import annotations

import pandas as pd

from .donnees import Donnees
from .outils import nombre
from .parametres import Parametres

CLES = {
    "clients": "id_client",
    "comptes": "id_compte",
    "operations": "id_operation",
    "alertes": "id_alerte",
    "declarations_soupcon": "id_ds",
    "declarations_especes": "id_dte",
    "liste_sanctions": "id_entree",
}


def controler_integrite(d: Donnees, p: Parametres) -> pd.DataFrame:
    lignes: list[dict] = []

    def ajouter(table: str, controle: str, resultat: str, statut: str, commentaire: str = "") -> None:
        lignes.append(
            {"table": table, "controle": controle, "resultat": resultat, "statut": statut, "commentaire": commentaire}
        )

    for nom, table in d.tables().items():
        cle = CLES[nom]
        ajouter(nom, "Nombre de lignes", nombre(len(table)), "INFO")
        doublons = int(table[cle].duplicated().sum())
        ajouter(nom, f"Doublons de clé ({cle})", nombre(doublons), "OK" if doublons == 0 else "ANOMALIE")
        vides = int(table[cle].isna().sum())
        ajouter(nom, f"Clé vide ({cle})", nombre(vides), "OK" if vides == 0 else "ANOMALIE")

    ops, comptes, clients = d.operations, d.comptes, d.clients
    debut, fin = ops["date_operation"].min(), ops["date_operation"].max()
    hors = int(
        (
            (ops["date_operation"] < p.periode_debut) | (ops["date_operation"] >= p.periode_fin + pd.Timedelta(days=1))
        ).sum()
    )
    ajouter(
        "operations",
        "Période couverte",
        f"{debut:%d/%m/%Y} au {fin:%d/%m/%Y}",
        "OK" if hors == 0 else "ANOMALIE",
        f"{hors} opération(s) hors période d'audit",
    )
    orphelines = int((~ops["id_compte"].isin(comptes["id_compte"])).sum())
    ajouter("operations", "Opérations sans compte connu", nombre(orphelines), "OK" if orphelines == 0 else "ANOMALIE")
    titulaire = ops["id_compte"].map(comptes.set_index("id_compte")["id_client"])
    incoherents = int((titulaire != ops["id_client"]).sum())
    ajouter(
        "operations",
        "Client de l'opération = titulaire du compte",
        nombre(incoherents),
        "OK" if incoherents == 0 else "ANOMALIE",
        "Nombre d'écarts",
    )
    negatifs = int((ops["montant"] <= 0).sum())
    ajouter("operations", "Montants nuls ou négatifs", nombre(negatifs), "OK" if negatifs == 0 else "ANOMALIE")
    sans_client = int((~comptes["id_client"].isin(clients["id_client"])).sum())
    ajouter("comptes", "Comptes sans client connu", nombre(sans_client), "OK" if sans_client == 0 else "ANOMALIE")
    alertes_orphelines = int(
        (d.alertes["id_operation"].notna() & ~d.alertes["id_operation"].isin(ops["id_operation"])).sum()
    )
    ajouter(
        "alertes",
        "Alertes liées à une opération inconnue",
        nombre(alertes_orphelines),
        "OK" if alertes_orphelines == 0 else "ANOMALIE",
    )

    credits = ops.loc[ops["sens"] == "C", "montant"].sum()
    debits = ops.loc[ops["sens"] == "D", "montant"].sum()
    ajouter(
        "operations",
        "Total des crédits de la période",
        f"{credits:,.0f} FCFA".replace(",", " "),
        "À RAPPROCHER",
        "À rapprocher de la balance / du grand livre à la date d'arrêté",
    )
    ajouter(
        "operations",
        "Total des débits de la période",
        f"{debits:,.0f} FCFA".replace(",", " "),
        "À RAPPROCHER",
        "À rapprocher de la balance / du grand livre à la date d'arrêté",
    )
    return pd.DataFrame(lignes)
