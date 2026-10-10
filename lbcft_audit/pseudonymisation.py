"""Pseudonymisation des données personnelles (secret bancaire, protection des données).

Sur des données réelles :
- les analyses tournent dans l'environnement sécurisé de la banque ;
- les livrables (Excel, tableau de bord, rapport) ne montrent que des identifiants
  internes ou des valeurs masquées / hachées ;
- le sel de hachage est fourni par la variable d'environnement LBCFT_SEL et n'est
  jamais enregistré dans le dépôt.
"""

from __future__ import annotations

import hashlib
import os

import pandas as pd


def sel() -> str:
    return os.environ.get("LBCFT_SEL", "sel-de-demonstration-a-remplacer")


def empreinte(valeur: object, longueur: int = 12) -> str:
    """Empreinte SHA-256 salée : même entrée => même empreinte, sans retour possible à la valeur."""
    if valeur is None or pd.isna(valeur):
        return ""
    return hashlib.sha256((sel() + str(valeur)).encode("utf-8")).hexdigest()[:longueur]


def masquer_nom(nom: object) -> str:
    """« Seydou KANTÉ » -> « S***** K**** » (garde la première lettre de chaque mot)."""
    if nom is None or pd.isna(nom):
        return ""
    return " ".join(m[0] + "*" * (len(m) - 1) for m in str(nom).split())


def pseudonymiser_table(
    table: pd.DataFrame,
    colonnes_noms=("nom_client", "nom_complet"),
    colonnes_hachees=("telephone", "adresse", "piece_numero"),
) -> pd.DataFrame:
    sortie = table.copy()
    for colonne in colonnes_noms:
        if colonne in sortie.columns:
            sortie[colonne] = sortie[colonne].map(masquer_nom)
    for colonne in colonnes_hachees:
        if colonne in sortie.columns:
            sortie[colonne] = sortie[colonne].map(empreinte)
    return sortie
