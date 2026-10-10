"""Bloc KYC — connaissance de la clientèle, PPE, bénéficiaires effectifs et filtrage des sanctions."""

from __future__ import annotations

from difflib import SequenceMatcher

import numpy as np
import pandas as pd

from .donnees import Donnees
from .outils import ResultatTest, normaliser_nom
from .parametres import Parametres

BLOC_KYC = "Connaissance client (KYC)"
BLOC_FILTRAGE = "Filtrage des sanctions"

CHAMPS_OBLIGATOIRES = {
    "PP": [
        "nom_complet",
        "date_naissance",
        "nationalite",
        "profession",
        "revenu_mensuel_declare",
        "adresse",
        "telephone",
        "piece_type",
        "piece_numero",
        "piece_date_expiration",
    ],
    "PM": [
        "nom_complet",
        "date_creation",
        "secteur_activite",
        "chiffre_affaires_annuel_declare",
        "adresse",
        "telephone",
        "piece_numero",
    ],
}


def _nb_operations(d: Donnees) -> pd.Series:
    return d.operations.groupby("id_client").size()


def kyc_01_completude(d: Donnees, p: Parametres) -> ResultatTest:
    """Champs d'identification et de profil obligatoires non renseignés."""
    lignes = []
    for type_client, champs in CHAMPS_OBLIGATOIRES.items():
        sous = d.clients[d.clients["type_client"] == type_client]
        manquants = sous[champs].isna()
        for idx in sous.index[manquants.any(axis=1)]:
            lignes.append(
                {
                    "id_client": sous.at[idx, "id_client"],
                    "type_client": type_client,
                    "agence": sous.at[idx, "agence"],
                    "nb_champs_manquants": int(manquants.loc[idx].sum()),
                    "champs_manquants": ", ".join(manquants.columns[manquants.loc[idx]]),
                }
            )
    exceptions = pd.DataFrame(
        lignes, columns=["id_client", "type_client", "agence", "nb_champs_manquants", "champs_manquants"]
    )
    par_agence = (
        d.clients.groupby("agence")
        .size()
        .rename("nb_clients")
        .to_frame()
        .join(exceptions.groupby("agence").size().rename("nb_dossiers_incomplets"))
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    par_agence["taux_incomplets"] = par_agence["nb_dossiers_incomplets"] / par_agence["nb_clients"]
    return ResultatTest(
        code="KYC-01",
        bloc=BLOC_KYC,
        titre="Complétude des données KYC obligatoires",
        objectif="Vérifier que les informations d'identification et de profil exigées sont renseignées.",
        references="Loi uniforme LBC/FT/FP, art. 16 et 17 ; Instruction BCEAO n°003-03-2025, art. 5 à 8.",
        parametres={
            "champs_PP": ", ".join(CHAMPS_OBLIGATOIRES["PP"]),
            "champs_PM": ", ".join(CHAMPS_OBLIGATOIRES["PM"]),
        },
        unite="clients",
        nb_population=len(d.clients),
        exceptions=exceptions,
        annexes={"par_agence": par_agence.sort_values("taux_incomplets", ascending=False)},
    )


def kyc_02_pieces_expirees(d: Donnees, p: Parametres) -> ResultatTest:
    """Pièces d'identité expirées à la date d'arrêté."""
    pp = d.clients[d.clients["type_client"] == "PP"]
    expirees = pp[pp["piece_date_expiration"] < p.date_arrete].copy()
    expirees["jours_depuis_expiration"] = (p.date_arrete - expirees["piece_date_expiration"]).dt.days
    expirees["operations_periode"] = expirees["id_client"].map(_nb_operations(d)).fillna(0).astype(int)
    colonnes = [
        "id_client",
        "agence",
        "piece_type",
        "piece_date_expiration",
        "jours_depuis_expiration",
        "operations_periode",
    ]
    return ResultatTest(
        code="KYC-02",
        bloc=BLOC_KYC,
        titre="Pièces d'identité expirées",
        objectif="Identifier les clients dont la pièce d'identité est expirée alors que la relation se poursuit.",
        references="Instruction BCEAO n°003-03-2025, art. 6 (pièce officielle en cours de validité) ; Loi uniforme, art. 19.",
        parametres={"date_arrete": f"{p.date_arrete:%d/%m/%Y}"},
        unite="clients",
        nb_population=len(pp),
        exceptions=expirees[colonnes].sort_values("jours_depuis_expiration", ascending=False).reset_index(drop=True),
    )


def kyc_03_revues_en_retard(d: Donnees, p: Parametres) -> ResultatTest:
    """Revues périodiques KYC non réalisées dans le délai fixé selon le niveau de risque."""
    periodicite = p.hypotheses["revue_kyc_annees"]
    c = d.clients.copy()
    annees = c["niveau_risque"].map(lambda r: int(periodicite.get(r, 1)))
    c["date_limite"] = [
        r + pd.DateOffset(years=a) if pd.notna(r) else pd.NaT for r, a in zip(c["date_derniere_revue_kyc"], annees)
    ]
    c["date_limite"] = pd.to_datetime(c["date_limite"])
    retard = c[c["date_derniere_revue_kyc"].isna() | (c["date_limite"] < p.date_arrete)].copy()
    retard["jours_de_retard"] = (p.date_arrete - retard["date_limite"]).dt.days
    colonnes = [
        "id_client",
        "type_client",
        "agence",
        "niveau_risque",
        "date_derniere_revue_kyc",
        "date_limite",
        "jours_de_retard",
    ]
    return ResultatTest(
        code="KYC-03",
        bloc=BLOC_KYC,
        titre="Revues KYC périodiques en retard",
        objectif="Vérifier la mise à jour périodique des dossiers selon le niveau de risque du client.",
        references=(
            "Loi uniforme LBC/FT/FP, art. 19 (mise à jour des informations) ; périodicité de la "
            "procédure interne (hypothèse : 1, 2 et 3 ans)."
        ),
        parametres={f"risque_{k.lower()}": f"{v} an(s)" for k, v in periodicite.items()},
        unite="clients",
        nb_population=len(c),
        exceptions=retard[colonnes].sort_values("jours_de_retard", ascending=False).reset_index(drop=True),
    )


def kyc_04_ppe(d: Donnees, p: Parametres) -> ResultatTest:
    """PPE : approbation de la haute direction, classification à risque élevé, réévaluation triennale."""
    annees = int(p.seuils["reevaluation_ppe_annees"])
    ppe = d.clients[d.clients["ppe"] == "OUI"].copy()
    limite = p.date_arrete - pd.DateOffset(years=annees)
    anomalies = pd.DataFrame(
        {
            "approbation_direction_absente": ppe["ppe_approbation_direction"].fillna("") != "OUI",
            "non_classee_risque_eleve": ppe["niveau_risque"] != "ELEVE",
            f"reevaluation_sup_{annees}_ans": ppe["date_derniere_revue_kyc"] < limite,
        },
        index=ppe.index,
    )
    ppe["anomalies"] = anomalies.apply(lambda r: ", ".join(r.index[r]), axis=1)
    ppe["nb_anomalies"] = anomalies.sum(axis=1)
    exceptions = ppe[ppe["nb_anomalies"] > 0]
    colonnes = [
        "id_client",
        "agence",
        "niveau_risque",
        "ppe_approbation_direction",
        "date_derniere_revue_kyc",
        "nb_anomalies",
        "anomalies",
    ]
    return ResultatTest(
        code="KYC-04",
        bloc=BLOC_KYC,
        titre="Personnes politiquement exposées (PPE)",
        objectif=(
            "Vérifier pour chaque PPE l'autorisation de la haute direction, la classification à risque "
            "élevé et la réévaluation du profil au moins tous les trois ans."
        ),
        references="Loi uniforme LBC/FT/FP, art. 29 (PPE) dont al. 3 (réévaluation tous les trois ans).",
        parametres={"reevaluation_ppe_annees": annees},
        unite="clients",
        nb_population=len(ppe),
        exceptions=exceptions[colonnes].reset_index(drop=True),
        annexes={
            "synthese_anomalies": anomalies.sum().rename("nb_ppe").reset_index().rename(columns={"index": "anomalie"})
        },
    )


def kyc_05_beneficiaires_effectifs(d: Donnees, p: Parametres) -> ResultatTest:
    """Personnes morales sans bénéficiaire effectif identifié."""
    pm = d.clients[d.clients["type_client"] == "PM"].copy()
    sans = pm[pm["beneficiaire_effectif_identifie"].fillna("NON") != "OUI"].copy()
    sans["operations_periode"] = sans["id_client"].map(_nb_operations(d)).fillna(0).astype(int)
    colonnes = [
        "id_client",
        "agence",
        "secteur_activite",
        "niveau_risque",
        "beneficiaire_effectif_identifie",
        "operations_periode",
    ]
    return ResultatTest(
        code="KYC-05",
        bloc=BLOC_KYC,
        titre="Bénéficiaires effectifs des personnes morales",
        objectif="Vérifier que le bénéficiaire effectif de chaque personne morale est identifié et vérifié.",
        references=(
            "Instruction BCEAO n°003-03-2025, art. 12 et art. 2 (seuil de détention de 25 %) ; "
            "Loi uniforme LBC/FT/FP, art. 25 (impossibilité de satisfaire aux obligations de vigilance)."
        ),
        parametres={"seuil_detention": "25 % du capital ou des droits de vote"},
        unite="clients",
        nb_population=len(pm),
        exceptions=sans[colonnes].reset_index(drop=True),
    )


def kyc_06_coherence_classification(d: Donnees, p: Parametres) -> ResultatTest:
    """Clients présentant des facteurs de risque élevé mais classés à un niveau trop bas."""
    c = d.clients.set_index("id_client")
    transferts = d.operations[d.operations["type_operation"].str.startswith("TRANSFERT")]
    exposes = set(transferts.loc[transferts["pays_contrepartie"].isin(p.pays_gafi), "id_client"])
    facteurs = pd.DataFrame(
        {
            "PPE": c["ppe"] == "OUI",
            "PM sans bénéficiaire effectif": (c["type_client"] == "PM")
            & (c["beneficiaire_effectif_identifie"] != "OUI"),
            "Flux avec un pays listé par le GAFI": c.index.isin(exposes),
        },
        index=c.index,
    )
    attendu = np.where(facteurs["PPE"], "ELEVE", np.where(facteurs.any(axis=1), "MOYEN ou ELEVE", ""))
    incoherent = (facteurs["PPE"] & (c["niveau_risque"] != "ELEVE")) | (
        facteurs.drop(columns="PPE").any(axis=1) & (c["niveau_risque"] == "FAIBLE")
    )
    exceptions = pd.DataFrame(
        {
            "id_client": c.index,
            "type_client": c["type_client"].to_numpy(),
            "agence": c["agence"].to_numpy(),
            "niveau_risque": c["niveau_risque"].to_numpy(),
            "niveau_attendu": attendu,
            "facteurs_de_risque": facteurs.apply(lambda r: ", ".join(r.index[r]), axis=1).to_numpy(),
        }
    )[incoherent.to_numpy()].reset_index(drop=True)
    return ResultatTest(
        code="KYC-06",
        bloc=BLOC_KYC,
        titre="Cohérence de la classification des risques",
        objectif="Vérifier que la classification des clients reflète leurs facteurs de risque élevé.",
        references=(
            "Loi uniforme LBC/FT/FP, art. 6 et 15 (approche fondée sur les risques), 29 (PPE) et 30 "
            "(pays à risque) ; Instruction BCEAO n°001-03-2025 (classification des risques)."
        ),
        parametres={"regle": "PPE => ELEVE ; autres facteurs => au moins MOYEN"},
        unite="clients",
        nb_population=int(facteurs.any(axis=1).sum()),
        exceptions=exceptions,
    )


def _score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def fil_01_filtrage_sanctions(d: Donnees, p: Parametres) -> ResultatTest:
    """Correspondances approchées entre les clients et la liste de sanctions (orthographe, ordre des noms)."""
    seuil = float(p.hypotheses["filtrage"]["score_min"])
    clients = d.clients.assign(nom_n=d.clients["nom_complet"].map(normaliser_nom))
    liste = d.liste_sanctions.assign(nom_n=d.liste_sanctions["nom"].map(normaliser_nom))
    lignes = []
    for _, entree in liste.iterrows():
        candidats = clients[clients["type_client"] == entree["type_entite"]]
        scores = candidats["nom_n"].map(lambda n: _score(n, entree["nom_n"]))
        for idx in scores.index[scores >= seuil]:
            cl = candidats.loc[idx]
            if entree["type_entite"] == "PM":
                qualification = "Correspondance forte (raison sociale)"
            elif pd.notna(cl["date_naissance"]) and cl["date_naissance"] == entree["date_naissance"]:
                qualification = "Correspondance forte (nom et date de naissance)"
            else:
                qualification = "Homonymie probable (date de naissance différente) : à lever"
            lignes.append(
                {
                    "id_client": cl["id_client"],
                    "nom_client": cl["nom_complet"],
                    "id_entree_liste": entree["id_entree"],
                    "nom_liste": entree["nom"],
                    "score_similarite": round(float(scores[idx]), 3),
                    "date_naissance_client": cl["date_naissance"],
                    "date_naissance_liste": entree["date_naissance"],
                    "qualification": qualification,
                    "resultat_filtrage_banque": cl["resultat_dernier_filtrage"],
                }
            )
    exceptions = pd.DataFrame(
        lignes,
        columns=[
            "id_client",
            "nom_client",
            "id_entree_liste",
            "nom_liste",
            "score_similarite",
            "date_naissance_client",
            "date_naissance_liste",
            "qualification",
            "resultat_filtrage_banque",
        ],
    )
    exceptions = exceptions.sort_values(["qualification", "score_similarite"], ascending=[True, False])
    non_signalees = int((exceptions["resultat_filtrage_banque"] == "AUCUNE_CORRESPONDANCE").sum())
    return ResultatTest(
        code="FIL-01",
        bloc=BLOC_FILTRAGE,
        titre="Filtrage des listes de sanctions (correspondances approchées)",
        objectif=(
            "Rejouer le filtrage de toute la clientèle contre la liste de sanctions avec une comparaison "
            "approchée (accents, ordre des noms, variantes d'orthographe, formes juridiques)."
        ),
        references=(
            "Instruction BCEAO n°001-03-2025, art. 6 (filtrage, sanctions ciblées « sans délai ») ; "
            "Loi uniforme LBC/FT/FP (gel des avoirs) ; recommandation 6 du GAFI."
        ),
        parametres={
            "score_min": seuil,
            "methode": "similarité de séquences sur noms normalisés et triés",
            "liste": "liste FICTIVE de démonstration",
        },
        unite="correspondances",
        nb_population=len(clients),
        exceptions=exceptions.reset_index(drop=True),
        commentaire=(
            f"{non_signalees} correspondance(s) sur {len(exceptions)} non signalée(s) par l'outil "
            "de filtrage de la banque lors du dernier filtrage."
        ),
    )


TESTS_KYC = [
    kyc_01_completude,
    kyc_02_pieces_expirees,
    kyc_03_revues_en_retard,
    kyc_04_ppe,
    kyc_05_beneficiaires_effectifs,
    kyc_06_coherence_classification,
    fil_01_filtrage_sanctions,
]
