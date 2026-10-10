"""Lecture et écriture des tables de données (CSV « ; », UTF-8 avec BOM pour Excel)."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

import pandas as pd

SEPARATEUR = ";"
ENCODAGE = "utf-8-sig"  # le BOM permet à Excel d'afficher correctement les accents

# Colonnes de dates par table (les autres colonnes texte restent en texte).
COLONNES_DATES: dict[str, list[str]] = {
    "clients": [
        "date_naissance",
        "date_creation",
        "date_entree_relation",
        "piece_date_expiration",
        "date_derniere_revue_kyc",
        "date_dernier_filtrage",
    ],
    "comptes": ["date_ouverture", "date_dernier_mouvement_avant_periode"],
    "operations": ["date_operation"],
    "alertes": ["date_alerte", "date_cloture"],
    "declarations_soupcon": ["date_alerte", "date_decision", "date_transmission"],
    "declarations_especes": ["date_operation", "date_declaration"],
    "liste_sanctions": ["date_naissance", "date_inscription"],
}
COLONNES_MONTANTS: dict[str, list[str]] = {
    "clients": ["revenu_mensuel_declare", "chiffre_affaires_annuel_declare"],
    "operations": ["montant"],
    "declarations_especes": ["montant_declare"],
}


@dataclass
class Donnees:
    """Tables extraites du système d'information de la banque (fictive)."""

    clients: pd.DataFrame
    comptes: pd.DataFrame
    operations: pd.DataFrame
    alertes: pd.DataFrame
    declarations_soupcon: pd.DataFrame
    declarations_especes: pd.DataFrame
    liste_sanctions: pd.DataFrame

    @classmethod
    def noms_tables(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    def tables(self) -> dict[str, pd.DataFrame]:
        return {nom: getattr(self, nom) for nom in self.noms_tables()}


def lire_table(chemin: Path, nom: str) -> pd.DataFrame:
    """Lit une table en forçant le texte, puis convertit dates et montants."""
    table = pd.read_csv(chemin, sep=SEPARATEUR, encoding=ENCODAGE, dtype=str, keep_default_na=False, na_values=[""])
    for colonne in COLONNES_DATES.get(nom, []):
        if colonne in table.columns:
            table[colonne] = pd.to_datetime(table[colonne], errors="coerce", format="ISO8601")
    for colonne in COLONNES_MONTANTS.get(nom, []):
        if colonne in table.columns:
            table[colonne] = pd.to_numeric(table[colonne], errors="coerce")
    return table


def charger_donnees(dossier: str | Path) -> Donnees:
    """Charge les sept tables d'un dossier (voir data/README.md pour le dictionnaire)."""
    dossier = Path(dossier)
    manquantes = [n for n in Donnees.noms_tables() if not (dossier / f"{n}.csv").exists()]
    if manquantes:
        raise FileNotFoundError(
            f"Tables absentes dans {dossier} : {', '.join(manquantes)}. Lancez d'abord : python -m lbcft_audit generer"
        )
    return Donnees(**{n: lire_table(dossier / f"{n}.csv", n) for n in Donnees.noms_tables()})


def ecrire_table(table: pd.DataFrame, chemin: Path) -> None:
    sortie = table.copy()
    for colonne in sortie.columns:
        if pd.api.types.is_datetime64_any_dtype(sortie[colonne]):
            avec_heure = (sortie[colonne].dropna().dt.normalize() != sortie[colonne].dropna()).any()
            format_date = "%Y-%m-%d %H:%M:%S" if avec_heure else "%Y-%m-%d"
            sortie[colonne] = sortie[colonne].dt.strftime(format_date)
    sortie.to_csv(chemin, sep=SEPARATEUR, encoding=ENCODAGE, index=False)


def sauvegarder_donnees(donnees: Donnees, dossier: str | Path) -> None:
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    for nom, table in donnees.tables().items():
        ecrire_table(table, dossier / f"{nom}.csv")
