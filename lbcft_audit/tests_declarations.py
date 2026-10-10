"""Blocs DEC et ALE — obligations déclaratives et traitement des alertes."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .donnees import Donnees
from .outils import ResultatTest
from .parametres import Parametres

BLOC_DEC = "Obligations déclaratives"
BLOC_ALE = "Traitement des alertes"


def dec_01_declarations_especes(d: Donnees, p: Parametres) -> ResultatTest:
    """Transactions en espèces atteignant le seuil sans déclaration (DTE) dans le registre."""
    seuil = float(p.seuils["declaration_especes_centif"])
    esp = d.operations[d.operations["type_operation"].isin(["VERSEMENT_ESPECES", "RETRAIT_ESPECES"])].copy()
    esp["jour"] = esp["date_operation"].dt.normalize()
    cle = ["id_client", "jour", "type_operation"]
    attendues = (
        esp.groupby(cle)
        .agg(
            montant_cumule=("montant", "sum"),
            nb_operations=("id_operation", "size"),
            agence=("agence_operation", "first"),
        )
        .reset_index()
    )
    attendues = attendues[attendues["montant_cumule"] >= seuil]
    registre = d.declarations_especes.rename(columns={"date_operation": "jour"})
    registre["jour"] = registre["jour"].dt.normalize()
    rapprochement = attendues.merge(registre[cle + ["id_dte"]], on=cle, how="left")
    manquantes = rapprochement[rapprochement["id_dte"].isna()].drop(columns="id_dte")
    manquantes = manquantes.rename(columns={"jour": "date_operation"}).reset_index(drop=True)
    par_agence = (
        attendues.groupby("agence")
        .size()
        .rename("dte_attendues")
        .to_frame()
        .join(manquantes.groupby("agence").size().rename("dte_manquantes"))
        .fillna(0)
        .astype(int)
    )
    par_agence["taux_manquantes"] = par_agence["dte_manquantes"] / par_agence["dte_attendues"]
    return ResultatTest(
        code="DEC-01",
        bloc=BLOC_DEC,
        titre="Déclarations des transactions en espèces (DTE)",
        objectif=(
            "Rapprocher les transactions en espèces atteignant le seuil (opération unique ou opérations "
            "liées d'une même journée) du registre des déclarations transmises à la CENTIF."
        ),
        references="Loi uniforme LBC/FT/FP, art. 72 ; Décision n°021 du 21/12/2023/CM/UMOA (seuil 15 M FCFA).",
        parametres={"seuil": int(seuil), "regle_de_liaison": "cumul par client, par jour et par sens (hypothèse)"},
        unite="déclarations",
        nb_population=len(attendues),
        exceptions=manquantes,
        montant_exceptions=float(manquantes["montant_cumule"].sum()),
        annexes={"par_agence": par_agence.reset_index().sort_values("taux_manquantes", ascending=False)},
        commentaire="Le délai réglementaire de transmission des DTE n'est pas testé (à préciser selon le texte national).",
    )


def ale_01_alertes_en_souffrance(d: Donnees, p: Parametres) -> ResultatTest:
    """Alertes encore ouvertes au-delà du délai de traitement de la procédure."""
    delai = int(p.hypotheses["alertes"]["delai_max_traitement_jours"])
    a = d.alertes.copy()
    a["age_jours"] = (p.date_arrete - a["date_alerte"]).dt.days
    ouvertes = a[a["statut"] == "OUVERTE"]
    retard = ouvertes[ouvertes["age_jours"] > delai].copy()
    retard["tranche"] = pd.cut(
        retard["age_jours"],
        bins=[delai, 60, 90, 180, 10_000],
        labels=[f"{delai + 1}-60 j", "61-90 j", "91-180 j", "> 180 j"],
    ).astype(str)
    par_analyste = (
        a.groupby("analyste")
        .size()
        .rename("alertes_recues")
        .to_frame()
        .join(ouvertes.groupby("analyste").size().rename("ouvertes"))
        .join(retard.groupby("analyste").size().rename("en_souffrance"))
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    colonnes = ["id_alerte", "id_client", "scenario", "date_alerte", "analyste", "age_jours", "tranche"]
    return ResultatTest(
        code="ALE-01",
        bloc=BLOC_ALE,
        titre="Alertes en souffrance",
        objectif="Mesurer l'arriéré d'alertes non traitées au-delà du délai fixé par la procédure.",
        references=(
            "Loi uniforme LBC/FT/FP, art. 21 et 60 (examen des opérations, déclaration immédiate) ; "
            "Instruction BCEAO n°001-03-2025, art. 6 ; délai interne de traitement (hypothèse)."
        ),
        parametres={"delai_max_traitement_jours": delai},
        unite="alertes",
        nb_population=len(a),
        exceptions=retard[colonnes].sort_values("age_jours", ascending=False).reset_index(drop=True),
        annexes={"par_analyste": par_analyste},
        commentaire=f"{len(ouvertes)} alerte(s) ouverte(s) à la date d'arrêté, dont {len(retard)} hors délai.",
    )


def ale_02_clotures_non_justifiees(d: Donnees, p: Parametres) -> ResultatTest:
    """Alertes clôturées sans motif, ou clôturées en masse par un même analyste le même jour."""
    seuil = int(p.hypotheses["alertes"]["seuil_clotures_massives"])
    a = d.alertes[d.alertes["statut"] == "CLOTUREE"].copy()
    a["jour_cloture"] = a["date_cloture"].dt.normalize()
    volume = a.groupby(["analyste", "jour_cloture"])["id_alerte"].transform("size")
    sans_motif = a["motif_cloture"].fillna("").str.strip() == ""
    massive = volume >= seuil
    a["anomalie"] = np.select(
        [sans_motif & massive, sans_motif, massive],
        ["Sans motif et clôture en masse", "Clôture sans motif", f"Clôture en masse (>= {seuil} le même jour)"],
        default="",
    )
    a["clotures_meme_jour"] = volume
    exceptions = a[a["anomalie"] != ""]
    colonnes = [
        "id_alerte",
        "id_client",
        "scenario",
        "date_alerte",
        "date_cloture",
        "analyste",
        "clotures_meme_jour",
        "motif_cloture",
        "anomalie",
    ]
    journees = a[massive].groupby(["analyste", "jour_cloture"]).size().rename("nb_clotures").reset_index()
    return ResultatTest(
        code="ALE-02",
        bloc=BLOC_ALE,
        titre="Clôtures d'alertes non justifiées ou en masse",
        objectif="Vérifier que chaque clôture d'alerte est motivée et résulte d'une analyse individuelle.",
        references=(
            "Loi uniforme LBC/FT/FP, art. 21 (rapport écrit confidentiel) et 23 (conservation) ; "
            "Instruction BCEAO n°001-03-2025, art. 6."
        ),
        parametres={"seuil_clotures_massives_par_jour": seuil},
        unite="alertes",
        nb_population=len(a),
        exceptions=exceptions[colonnes].sort_values(["anomalie", "date_cloture"]).reset_index(drop=True),
        annexes={"journees_de_cloture_massive": journees},
    )


def ale_03_delais_declarations_soupcon(d: Donnees, p: Parametres) -> ResultatTest:
    """Délais entre l'alerte, la décision de déclarer et la transmission à la CENTIF."""
    h = p.hypotheses["declarations_soupcon"]
    ds = d.declarations_soupcon.copy()
    ds["delai_analyse_jours"] = (ds["date_decision"] - ds["date_alerte"]).dt.days
    ds["delai_transmission_jours"] = (ds["date_transmission"] - ds["date_decision"]).dt.days
    analyse = ds["delai_analyse_jours"] > h["delai_max_analyse_jours"]
    transmission = ds["delai_transmission_jours"] > h["delai_max_transmission_jours"]
    ds["anomalie"] = np.select(
        [analyse & transmission, analyse, transmission],
        ["Analyse et transmission tardives", "Analyse tardive", "Transmission tardive"],
        default="",
    )
    colonnes = [
        "id_ds",
        "id_alerte",
        "id_client",
        "date_alerte",
        "date_decision",
        "date_transmission",
        "delai_analyse_jours",
        "delai_transmission_jours",
        "anomalie",
    ]
    exceptions = ds.loc[ds["anomalie"] != "", colonnes].reset_index(drop=True)
    return ResultatTest(
        code="ALE-03",
        bloc=BLOC_ALE,
        titre="Délais des déclarations de soupçon (DS)",
        objectif="Mesurer les délais d'analyse et de transmission des déclarations de soupçon à la CENTIF.",
        references=(
            "Loi uniforme LBC/FT/FP, art. 60 (déclaration « immédiate ») et 61 ; délais internes "
            "retenus comme critères d'audit (hypothèses)."
        ),
        parametres={
            "delai_max_analyse_jours": h["delai_max_analyse_jours"],
            "delai_max_transmission_jours": h["delai_max_transmission_jours"],
        },
        unite="déclarations",
        nb_population=len(ds),
        exceptions=exceptions,
        annexes={"distribution_delais": ds[["id_ds", "delai_analyse_jours", "delai_transmission_jours"]]},
        commentaire=(
            f"Délai médian d'analyse : {ds['delai_analyse_jours'].median():.0f} jours ; "
            f"délai médian de transmission : {ds['delai_transmission_jours'].median():.0f} jour(s)."
        ),
    )


TESTS_DECLARATIONS = [
    dec_01_declarations_especes,
    ale_01_alertes_en_souffrance,
    ale_02_clotures_non_justifiees,
    ale_03_delais_declarations_soupcon,
]
