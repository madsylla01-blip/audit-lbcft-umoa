"""Chargement des paramètres de la mission (config/parametres.yaml)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_PARAMETRES = RACINE / "config" / "parametres.yaml"


@dataclass
class Parametres:
    """Accès simple aux paramètres ; `brut` conserve le dictionnaire YAML complet."""

    brut: dict[str, Any]

    def __getitem__(self, cle: str) -> Any:
        return self.brut[cle]

    def copie(self) -> "Parametres":
        return Parametres(copy.deepcopy(self.brut))

    # --- Mission -----------------------------------------------------------
    @property
    def banque(self) -> str:
        return self.brut["mission"]["banque"]

    @property
    def periode_debut(self) -> pd.Timestamp:
        return pd.Timestamp(self.brut["mission"]["periode_debut"])

    @property
    def periode_fin(self) -> pd.Timestamp:
        return pd.Timestamp(self.brut["mission"]["periode_fin"])

    @property
    def date_arrete(self) -> pd.Timestamp:
        return pd.Timestamp(self.brut["mission"]["date_arrete"])

    # --- Dossiers ----------------------------------------------------------
    @property
    def dossier_donnees(self) -> Path:
        return _chemin(self.brut["donnees"]["dossier"])

    @property
    def dossier_sorties(self) -> Path:
        return _chemin(self.brut["donnees"]["dossier_sorties"])

    # --- Raccourcis --------------------------------------------------------
    @property
    def graine(self) -> int:
        return int(self.brut["generation"]["graine"])

    @property
    def seuils(self) -> dict[str, Any]:
        return self.brut["seuils_reglementaires"]

    @property
    def hypotheses(self) -> dict[str, Any]:
        return self.brut["hypotheses_audit"]

    @property
    def pays_gafi(self) -> set[str]:
        listes = self.brut["listes_gafi"]
        return set(listes["appel_a_action"]) | set(listes["surveillance_renforcee"])

    @property
    def pays_liste_banque(self) -> set[str]:
        return set(self.brut["parametrage_banque"]["liste_pays_a_risque"])


def _chemin(valeur: str) -> Path:
    chemin = Path(valeur)
    return chemin if chemin.is_absolute() else RACINE / chemin


def charger_parametres(chemin: str | Path | None = None) -> Parametres:
    """Lit le fichier YAML de paramètres (par défaut config/parametres.yaml)."""
    chemin = Path(chemin) if chemin else CHEMIN_PARAMETRES
    with open(chemin, encoding="utf-8") as fichier:
        return Parametres(yaml.safe_load(fichier))
