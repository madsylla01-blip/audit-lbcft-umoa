"""Fixtures partagées par les tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from lbcft_audit.donnees import Donnees  # noqa: E402
from lbcft_audit.moteur import executer_audit  # noqa: E402
from lbcft_audit.parametres import charger_parametres  # noqa: E402

COLONNES = {
    "clients": [
        "id_client",
        "type_client",
        "nom_complet",
        "date_naissance",
        "date_creation",
        "nationalite",
        "profession",
        "secteur_activite",
        "revenu_mensuel_declare",
        "chiffre_affaires_annuel_declare",
        "telephone",
        "adresse",
        "agence",
        "date_entree_relation",
        "niveau_risque",
        "ppe",
        "ppe_approbation_direction",
        "piece_type",
        "piece_numero",
        "piece_date_expiration",
        "beneficiaire_effectif_identifie",
        "date_derniere_revue_kyc",
        "date_dernier_filtrage",
        "resultat_dernier_filtrage",
    ],
    "comptes": [
        "id_compte",
        "id_client",
        "type_compte",
        "devise",
        "agence",
        "date_ouverture",
        "date_dernier_mouvement_avant_periode",
        "statut",
    ],
    "operations": [
        "id_operation",
        "date_operation",
        "id_compte",
        "id_client",
        "type_operation",
        "sens",
        "montant",
        "canal",
        "agence_operation",
        "pays_contrepartie",
        "contrepartie",
        "libelle",
    ],
    "alertes": [
        "id_alerte",
        "id_client",
        "id_operation",
        "scenario",
        "date_alerte",
        "analyste",
        "statut",
        "date_cloture",
        "motif_cloture",
        "decision",
    ],
    "declarations_soupcon": [
        "id_ds",
        "id_alerte",
        "id_client",
        "date_alerte",
        "date_decision",
        "date_transmission",
        "statut",
    ],
    "declarations_especes": [
        "id_dte",
        "id_client",
        "date_operation",
        "type_operation",
        "montant_declare",
        "date_declaration",
    ],
    "liste_sanctions": ["id_entree", "nom", "type_entite", "date_naissance", "programme", "date_inscription"],
}
DATES = {
    "date_naissance",
    "date_creation",
    "date_entree_relation",
    "piece_date_expiration",
    "date_derniere_revue_kyc",
    "date_dernier_filtrage",
    "date_ouverture",
    "date_dernier_mouvement_avant_periode",
    "date_operation",
    "date_alerte",
    "date_cloture",
    "date_decision",
    "date_transmission",
    "date_declaration",
    "date_inscription",
}


def table(nom: str, lignes: list[dict] | None = None) -> pd.DataFrame:
    """Construit une table au bon format à partir de quelques lignes (colonnes absentes = vides)."""
    df = pd.DataFrame(lignes or [], columns=COLONNES[nom])
    for colonne in df.columns:
        if colonne in DATES:
            df[colonne] = pd.to_datetime(df[colonne])
        elif colonne in ("montant", "montant_declare", "revenu_mensuel_declare", "chiffre_affaires_annuel_declare"):
            df[colonne] = pd.to_numeric(df[colonne])
    return df


def client(id_client: str, **valeurs) -> dict:
    base = {
        "id_client": id_client,
        "type_client": "PP",
        "nom_complet": f"Client {id_client}",
        "date_naissance": "1985-01-01",
        "nationalite": "SN",
        "profession": "Commerçant(e)",
        "revenu_mensuel_declare": 500_000,
        "telephone": f"7{id_client[-7:]:0>7}",
        "adresse": f"Lot {id_client}",
        "agence": "AG01",
        "date_entree_relation": "2015-01-01",
        "niveau_risque": "FAIBLE",
        "ppe": "NON",
        "piece_type": "CNI",
        "piece_numero": "A1234567",
        "piece_date_expiration": "2030-01-01",
        "date_derniere_revue_kyc": "2025-01-01",
        "date_dernier_filtrage": "2026-06-29",
        "resultat_dernier_filtrage": "AUCUNE_CORRESPONDANCE",
    }
    base.update(valeurs)
    return base


def donnees(**tables) -> Donnees:
    return Donnees(**{nom: tables.get(nom, table(nom)) for nom in COLONNES})


@pytest.fixture(scope="session")
def parametres():
    return charger_parametres()


@pytest.fixture(scope="session")
def resultats(parametres):
    return executer_audit(p=parametres)


@pytest.fixture(scope="session")
def meta(parametres):
    with open(parametres.dossier_donnees / "metadonnees_generation.json", encoding="utf-8") as f:
        return json.load(f)
