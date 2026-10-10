"""Fonctions utilitaires partagées (normalisation de texte, formats, structure de résultat)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

FORMES_JURIDIQUES = {"SARL", "SARLU", "SA", "SAS", "SASU", "ETS", "GIE", "SCI", "LLC", "LTD", "FZE", "CO", "INC"}


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))


def normaliser_nom(nom: object, retirer_formes: bool = True) -> str:
    """Majuscules, sans accents ni ponctuation, formes juridiques retirées, mots triés.

    Le tri des mots rend la comparaison insensible à l'ordre « Prénom NOM » / « NOM Prénom ».
    """
    if nom is None or (isinstance(nom, float) and pd.isna(nom)) or nom is pd.NA:
        return ""
    texte = re.sub(r"[^A-Z0-9 ]", " ", sans_accents(str(nom)).upper())
    mots = [m for m in texte.split() if not (retirer_formes and m in FORMES_JURIDIQUES)]
    return " ".join(sorted(mots))


def normaliser_adresse(adresse: object) -> str:
    if adresse is None or pd.isna(adresse):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", sans_accents(str(adresse)).lower())).strip()


def normaliser_telephone(telephone: object) -> str:
    if telephone is None or pd.isna(telephone):
        return ""
    return re.sub(r"\D", "", str(telephone))[-8:]


def fcfa(montant: float | int | None, unite: str = "") -> str:
    """Formate un montant : 12 500 000 FCFA, ou 12,5 M FCFA avec unite='M'."""
    if montant is None or pd.isna(montant):
        return "—"
    if unite == "M":
        return f"{montant / 1e6:,.1f} M FCFA".replace(",", " ").replace(".", ",")
    if unite == "Md":
        return f"{montant / 1e9:,.2f} Md FCFA".replace(",", " ").replace(".", ",")
    return f"{montant:,.0f} FCFA".replace(",", " ")


def nombre(valeur: float | int) -> str:
    return f"{valeur:,.0f}".replace(",", " ")


def pourcentage(part: float, total: float, decimales: int = 0) -> str:
    if not total:
        return "—"
    return f"{100 * part / total:.{decimales}f} %".replace(".", ",")


@dataclass
class ResultatTest:
    """Résultat d'un test d'audit : paramètres, population, exceptions et annexes."""

    code: str
    bloc: str
    titre: str
    objectif: str
    references: str
    parametres: dict
    unite: str  # grain des exceptions : clients, opérations, alertes...
    nb_population: int
    exceptions: pd.DataFrame
    montant_exceptions: float | None = None
    detail: pd.DataFrame | None = None  # opérations sous-jacentes (pour l'analyse)
    annexes: dict[str, pd.DataFrame] = field(default_factory=dict)
    commentaire: str = ""

    @property
    def nb_exceptions(self) -> int:
        return len(self.exceptions)

    @property
    def clients(self) -> set[str]:
        if "id_client" not in self.exceptions.columns:
            return set()
        return set(self.exceptions["id_client"].dropna().astype(str))

    @property
    def taux(self) -> float:
        return self.nb_exceptions / self.nb_population if self.nb_population else 0.0


def accord(nombre_elements: int, singulier: str, pluriel: str | None = None) -> str:
    """accord(1, "alerte") -> "1 alerte" ; accord(3, "alerte") -> "3 alertes"."""
    mot = singulier if abs(nombre_elements) < 2 else (pluriel or singulier + "s")
    return f"{nombre(nombre_elements)} {mot}"


def decimal_fr(valeur: float, decimales: int = 2) -> str:
    return f"{valeur:.{decimales}f}".replace(".", ",")


PAYS = {
    "AE": "Émirats arabes unis",
    "AO": "Angola",
    "BA": "Bosnie-Herzégovine",
    "BE": "Belgique",
    "BF": "Burkina Faso",
    "BG": "Bulgarie",
    "BJ": "Bénin",
    "BO": "Bolivie",
    "CA": "Canada",
    "CD": "RD Congo",
    "CI": "Côte d'Ivoire",
    "CM": "Cameroun",
    "CN": "Chine",
    "DE": "Allemagne",
    "ES": "Espagne",
    "FR": "France",
    "GA": "Gabon",
    "GH": "Ghana",
    "GN": "Guinée",
    "GW": "Guinée-Bissau",
    "HT": "Haïti",
    "IN": "Inde",
    "IQ": "Irak",
    "IR": "Iran",
    "IT": "Italie",
    "KE": "Kenya",
    "KP": "Corée du Nord",
    "KW": "Koweït",
    "LA": "Laos",
    "LB": "Liban",
    "MA": "Maroc",
    "MC": "Monaco",
    "ML": "Mali",
    "MM": "Myanmar",
    "MZ": "Mozambique",
    "NA": "Namibie",
    "NE": "Niger",
    "NG": "Nigeria",
    "NP": "Népal",
    "PG": "Papouasie-Nouvelle-Guinée",
    "SN": "Sénégal",
    "SS": "Soudan du Sud",
    "SY": "Syrie",
    "TG": "Togo",
    "TR": "Turquie",
    "US": "États-Unis",
    "VE": "Venezuela",
    "VG": "Îles Vierges britanniques",
    "VN": "Viêt Nam",
    "YE": "Yémen",
    "ZA": "Afrique du Sud",
}


def nom_pays(code: object) -> str:
    if code is None or pd.isna(code):
        return ""
    return PAYS.get(str(code), str(code))
