"""Génération d'un jeu de données 100 % fictif : la Banque Fictive de l'Union (BFU).

Le jeu reproduit douze mois d'activité d'une banque de détail de l'UMOA :
clients, comptes, opérations, alertes produites par l'outil de surveillance de la
banque, registres des déclarations (soupçon et espèces) et une liste de sanctions
fictive.

Des typologies connues de blanchiment et des anomalies de processus sont injectées
volontairement. Leur liste est écrite dans `verite_terrain.csv` et
`metadonnees_generation.json` ; ces deux fichiers servent UNIQUEMENT à mesurer la
performance des tests d'audit (tests unitaires, docs/08). Les tests d'audit ne les
lisent jamais.

Aucune donnée réelle n'est utilisée. Toute ressemblance avec des personnes ou des
entités existantes serait fortuite.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from .donnees import Donnees, ecrire_table, sauvegarder_donnees
from .parametres import Parametres, charger_parametres

# ---------------------------------------------------------------------------
# Référentiels fictifs
# ---------------------------------------------------------------------------
AGENCES = {
    "AG01": "Agence Centrale",
    "AG02": "Agence Grand Marché",
    "AG03": "Agence Zone Portuaire",
    "AG04": "Agence Université",
    "AG05": "Agence Zone Industrielle",
    "AG06": "Agence Aéroport",
}
POIDS_AGENCES = [0.26, 0.20, 0.16, 0.12, 0.14, 0.12]
ANALYSTES = ["A01", "A02", "A03", "A04", "A05"]

PRENOMS_H = [
    "Abdoulaye",
    "Moussa",
    "Mamadou",
    "Seydou",
    "Boubacar",
    "Ousmane",
    "Souleymane",
    "Adama",
    "Issa",
    "Yacouba",
    "Lassina",
    "Kouassi",
    "Koffi",
    "Yao",
    "Kodjo",
    "Komlan",
    "Sènou",
    "Amadou",
    "Cheick",
    "Bakary",
    "Drissa",
    "Karim",
    "Salif",
    "Fousseni",
    "Hamidou",
    "Idrissa",
    "Aliou",
    "Modou",
    "Hervé",
    "Rodrigue",
]
PRENOMS_F = [
    "Aminata",
    "Fatoumata",
    "Mariam",
    "Awa",
    "Kadiatou",
    "Aïssata",
    "Salimata",
    "Rokia",
    "Adjoa",
    "Akissi",
    "Afi",
    "Ablavi",
    "Mariama",
    "Ndèye",
    "Fanta",
    "Assétou",
    "Rasmata",
    "Haoua",
    "Ramatou",
    "Bintou",
    "Djénéba",
    "Oumou",
    "Coumba",
    "Khady",
    "Nafissatou",
    "Safiatou",
    "Zénabou",
    "Edwige",
    "Clarisse",
    "Mireille",
]
NOMS = [
    "Traoré",
    "Diallo",
    "Koné",
    "Ouédraogo",
    "Sawadogo",
    "Coulibaly",
    "Diarra",
    "Sow",
    "Ndiaye",
    "Diop",
    "Fall",
    "Kouassi",
    "Kouamé",
    "Konan",
    "Mensah",
    "Agbodjan",
    "Adjovi",
    "Hounkpatin",
    "Maïga",
    "Cissé",
    "Sanogo",
    "Dembélé",
    "Kaboré",
    "Zongo",
    "Bâ",
    "Sy",
    "Guèye",
    "Faye",
    "Kane",
    "Diakité",
    "Doumbia",
    "Touré",
    "Ouattara",
    "Soro",
    "Tall",
    "Sidibé",
    "Djibo",
    "Tchao",
    "Amégan",
    "Kpodar",
    "Gnonlonfoun",
    "Dossou",
    "Akakpo",
    "Somé",
    "Yéo",
    "Tiendrébéogo",
]
# Combinaisons écartées car portées par des personnalités publiques connues.
NOMS_ECARTES = {
    "moussa traore",
    "adama traore",
    "aminata toure",
    "abdoulaye diop",
    "amadou toure",
    "mamadou diallo",
    "salif traore",
    "ousmane sy",
    "aminata diallo",
}
QUARTIERS = [
    "Quartier Commerce",
    "Cité Administrative",
    "Zone Industrielle",
    "Quartier Résidentiel",
    "Cité Universitaire",
    "Quartier du Port",
    "Nouveau Quartier",
    "Quartier des Affaires",
    "Cité Sociale",
    "Quartier Marché",
    "Cité des Cadres",
    "Quartier Gare",
]
PM_PREFIXES = [
    "SAHEL",
    "SAVANE",
    "BAOBAB",
    "LAGUNE",
    "KARITE",
    "HARMATTAN",
    "TERANGA",
    "AKWABA",
    "DELTA",
    "ETOILE",
    "HORIZON",
    "NIOKOLO",
    "FALEME",
    "MONO",
    "OTI",
    "KOMOE",
    "BANI",
    "BANDAMA",
]
PM_ACTIVITES = {
    "Commerce général": ["NEGOCE", "DISTRIBUTION", "COMMERCE GENERAL"],
    "BTP": ["BTP", "CONSTRUCTION", "TRAVAUX"],
    "Import-export": ["IMPORT-EXPORT", "TRADING", "INTERNATIONAL"],
    "Transport et logistique": ["TRANSPORT", "LOGISTIQUE", "TRANSIT"],
    "Agro-industrie": ["AGRO", "AGRICULTURE", "INDUSTRIES ALIMENTAIRES"],
    "Services": ["SERVICES", "CONSEIL", "TECHNOLOGIES"],
    "Immobilier": ["IMMOBILIER", "PROMOTION IMMOBILIERE", "HABITAT"],
}
PM_FORMES = ["SARL", "SA", "SAS", "SARLU", "ETS"]

# (profession, revenu mensuel min, max, profil d'activité, poids, versements espèces / mois)
PROFESSIONS = [
    ("Fonctionnaire", 250_000, 900_000, "salarie", 0.14, 0),
    ("Enseignant(e)", 200_000, 650_000, "salarie", 0.10, 0),
    ("Cadre du secteur privé", 600_000, 3_000_000, "salarie", 0.12, 0),
    ("Retraité(e)", 100_000, 600_000, "salarie", 0.06, 0),
    ("Commerçant(e)", 300_000, 4_000_000, "especes", 0.20, 6),
    ("Artisan", 150_000, 800_000, "especes", 0.08, 3),
    ("Transporteur", 200_000, 1_200_000, "especes", 0.06, 4),
    ("Agriculteur / Éleveur", 100_000, 1_500_000, "especes", 0.05, 2),
    ("Profession libérale", 800_000, 5_000_000, "mixte", 0.05, 0),
    ("Étudiant(e)", 25_000, 80_000, "faible", 0.08, 0),
    ("Sans activité", 25_000, 60_000, "faible", 0.06, 0),
]
# (secteur, CA annuel min, max, profil d'activité, poids)
SECTEURS = [
    ("Commerce général", 100e6, 1.5e9, "pm_especes", 0.24),
    ("BTP", 200e6, 4e9, "pm_virements", 0.14),
    ("Import-export", 300e6, 6e9, "pm_international", 0.16),
    ("Transport et logistique", 100e6, 2e9, "pm_virements", 0.12),
    ("Agro-industrie", 200e6, 3e9, "pm_virements", 0.12),
    ("Services", 50e6, 1e9, "pm_virements", 0.14),
    ("Immobilier", 100e6, 2e9, "pm_virements", 0.08),
]
NATIONALITES = {
    "SN": 0.18,
    "ML": 0.16,
    "BF": 0.14,
    "CI": 0.14,
    "BJ": 0.10,
    "TG": 0.09,
    "NE": 0.08,
    "GW": 0.03,
    "GN": 0.03,
    "FR": 0.02,
    "LB": 0.01,
    "CN": 0.01,
    "NG": 0.01,
}
# Pays des transferts « normaux » (commerce international et diaspora).
POOL_COMMERCE = {
    "CN": 0.22,
    "FR": 0.17,
    "AE": 0.12,
    "IN": 0.06,
    "TR": 0.07,
    "BE": 0.04,
    "DE": 0.03,
    "ES": 0.03,
    "IT": 0.03,
    "US": 0.03,
    "MA": 0.05,
    "GH": 0.03,
    "NG": 0.05,
    "BF": 0.02,
    "ZA": 0.02,
    "VN": 0.01,
    "CM": 0.01,
    "SN": 0.02,
    "ML": 0.02,
    "BJ": 0.01,
    "TG": 0.01,
}
POOL_DIASPORA = {
    "FR": 0.35,
    "US": 0.15,
    "IT": 0.12,
    "ES": 0.10,
    "BE": 0.08,
    "DE": 0.05,
    "CA": 0.05,
    "AE": 0.05,
    "GA": 0.05,
}

# Plan d'activité normale : (type d'opération, intensité mensuelle, loi du montant).
# Montant = base mensuelle (revenu ou CA/12) x facteur ; loi "u" = uniforme [a, b],
# "ln" = a x lognormale(0, b), "ln_k" = a / k x lognormale(0, b) où k est l'intensité.
SPECS = {
    "salarie": [
        ("SALAIRE", 1.0, ("u", 0.97, 1.03)),
        ("VIREMENT_RECU", 0.3, ("u", 0.1, 0.6)),
        ("RETRAIT_ESPECES", 2.0, ("u", 0.08, 0.3)),
        ("VIREMENT_EMIS", 1.0, ("u", 0.05, 0.35)),
        ("VERSEMENT_ESPECES", 0.4, ("u", 0.05, 0.5)),
    ],
    "especes": [
        ("VERSEMENT_ESPECES", "k", ("ln_k", 1.2, 0.35)),
        ("RETRAIT_ESPECES", 2.0, ("u", 0.1, 0.35)),
        ("VIREMENT_EMIS", 1.2, ("u", 0.1, 0.5)),
        ("VIREMENT_RECU", 0.4, ("u", 0.1, 0.6)),
    ],
    "mixte": [
        ("VIREMENT_RECU", 3.0, ("ln", 0.33, 0.35)),
        ("VERSEMENT_ESPECES", 1.0, ("u", 0.1, 0.4)),
        ("RETRAIT_ESPECES", 2.0, ("u", 0.08, 0.3)),
        ("VIREMENT_EMIS", 2.0, ("u", 0.1, 0.4)),
    ],
    "faible": [
        ("VIREMENT_RECU", 1.0, ("u", 0.5, 1.5)),
        ("RETRAIT_ESPECES", 1.5, ("u", 0.2, 0.6)),
        ("VERSEMENT_ESPECES", 0.2, ("u", 0.2, 1.0)),
    ],
    "pm_especes": [
        ("VERSEMENT_ESPECES", 10.0, ("ln", 0.45 / 10, 0.45)),
        ("VIREMENT_RECU", 4.0, ("ln", 0.55 / 4, 0.35)),
        ("VIREMENT_EMIS", 6.0, ("ln", 0.9 / 6, 0.35)),
        ("RETRAIT_ESPECES", 2.0, ("u", 0.015, 0.045)),
    ],
    "pm_virements": [
        ("VIREMENT_RECU", 4.0, ("ln", 0.25, 0.35)),
        ("VIREMENT_EMIS", 5.0, ("ln", 0.18, 0.35)),
        ("VERSEMENT_ESPECES", 0.8, ("u", 0.01, 0.03)),
        ("RETRAIT_ESPECES", 1.5, ("u", 0.01, 0.03)),
    ],
    "pm_international": [
        ("VIREMENT_RECU", 4.0, ("ln", 0.2, 0.35)),
        ("VIREMENT_EMIS", 3.0, ("ln", 0.12, 0.35)),
        ("TRANSFERT_INT_EMIS", 1.5, ("ln", 0.25, 0.4)),
        ("TRANSFERT_INT_RECU", 0.3, ("u", 0.05, 0.15)),
        ("VERSEMENT_ESPECES", 0.5, ("u", 0.01, 0.03)),
        ("RETRAIT_ESPECES", 1.0, ("u", 0.01, 0.03)),
    ],
}
SENS = {
    "VERSEMENT_ESPECES": "C",
    "RETRAIT_ESPECES": "D",
    "VIREMENT_RECU": "C",
    "VIREMENT_EMIS": "D",
    "TRANSFERT_INT_RECU": "C",
    "TRANSFERT_INT_EMIS": "D",
}
HEURES = {"GUICHET": (8, 16), "GAB": (6, 22), "BANQUE_DIGITALE": (7, 22), "VIREMENT": (8, 17), "SWIFT": (9, 15)}

# Liste de sanctions FICTIVE (aucun lien avec une liste officielle).
SANCTIONS_PP = [
    ("Bourama", "BAGAYOKO", "1971-04-02"),
    ("Sidiki", "TAMBOURA", "1966-08-19"),
    ("Yaya", "SAMASSEKOU", "1980-01-27"),
    ("Hamadoun", "BOCOUM", "1975-12-05"),
    ("Siaka", "TOGOLA", "1969-03-14"),
    ("Brahima", "DIABAGATE", "1984-07-22"),
    ("Kassoum", "KAMBIRE", "1977-10-09"),
    ("Mamoudou", "SANOU", "1962-06-30"),
    ("Tiémoko", "NIKIEMA", "1979-02-11"),
    ("Bréhima", "SOMDA", "1986-09-03"),
    ("Daouda", "HIEN", "1973-05-25"),
    ("Lamine", "PODA", "1968-11-17"),
    ("Sanata", "DABIRE", "1981-08-08"),
    ("Bibata", "KIENTEGA", "1990-12-20"),
    ("Mahamane", "DJIBRILA", "1983-02-17"),
    ("Seydou", "KANTE", "1979-11-04"),
    ("Aminata", "SANGARE", "1968-09-30"),
    ("Gaoussou", "FOFANA", "1974-04-12"),
    ("Nouhoum", "DOSSO", "1972-07-07"),
    ("Zoumana", "KAMATE", "1985-03-29"),
    ("Issiaka", "BADO", "1970-10-15"),
    ("Dramane", "ZIDA", "1976-06-21"),
    ("Mariétou", "KONATE", "1988-01-09"),
    ("Lacina", "TOGO", "1964-09-12"),
    ("Abibata", "SERE", "1987-05-02"),
    ("Fatimata", "BARRO", "1991-11-26"),
    ("Moctar", "DICKO", "1967-02-28"),
    ("Inoussa", "OUATTARA-BAKO", "1978-08-16"),
]
SANCTIONS_PM = [
    "KORALIS NEGOCE",
    "VELDRAN TRADING",
    "ZANTHEO LOGISTICS",
    "MIRALUX COMMODITIES",
    "ORVANE CAPITAL",
    "QUELLAR SERVICES",
    "TRAVENOR IMPEX",
    "SOLVARA MINING",
    "BRAXTEL INVEST",
    "NERIDA SHIPPING",
]


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c))


class _Generateur:
    """Construit le jeu de données étape par étape (graine fixe => résultat reproductible)."""

    def __init__(self, p: Parametres):
        self.p = p
        self.rng = np.random.default_rng(p.graine)
        self.debut = p.periode_debut
        self.fin = p.periode_fin
        self.arrete = p.date_arrete
        self.seuil_dte = float(p.seuils["declaration_especes_centif"])
        self.ops_injectees: list[dict] = []
        self.verite: list[dict] = []
        self.meta: dict[str, object] = {"graine": p.graine}

    # ------------------------------------------------------------------ outils
    def _choix(self, valeurs, taille=None, poids=None):
        poids = None if poids is None else np.asarray(poids, dtype=float) / np.sum(poids)
        return self.rng.choice(valeurs, size=taille, p=poids)

    def _pays(self, pool: dict[str, float], taille=None):
        return self._choix(list(pool), taille, list(pool.values()))

    def _date_aleatoire(self, debut: pd.Timestamp, fin: pd.Timestamp) -> pd.Timestamp:
        jours = max((fin - debut).days, 0)
        return debut + pd.Timedelta(days=int(self.rng.integers(0, jours + 1)))

    def _heure(self, jour: pd.Timestamp, canal: str) -> pd.Timestamp:
        h_min, h_max = HEURES[canal]
        return jour.normalize() + pd.Timedelta(
            hours=int(self.rng.integers(h_min, h_max + 1)),
            minutes=int(self.rng.integers(0, 60)),
            seconds=int(self.rng.integers(0, 60)),
        )

    def _nom_pp(self, sexe: str) -> tuple[str, str]:
        while True:
            prenom = str(self._choix(PRENOMS_H if sexe == "M" else PRENOMS_F))
            nom = str(self._choix(NOMS))
            if _sans_accents(f"{prenom} {nom}").lower() not in NOMS_ECARTES:
                # 70 % des noms sont saisis en majuscules sans accents, comme dans beaucoup de SI
                nom_saisi = _sans_accents(nom).upper() if self.rng.random() < 0.7 else nom.upper()
                return prenom, nom_saisi

    def _nom_pm(self, secteur: str, deja: set[str]) -> str:
        while True:
            nom = f"{self._choix(PM_PREFIXES)} {self._choix(PM_ACTIVITES[secteur])} {self._choix(PM_FORMES)}"
            if nom not in deja:
                deja.add(nom)
                return nom

    def _verite(self, id_client: str, typologie: str, detail: str) -> None:
        self.verite.append({"id_client": id_client, "typologie": typologie, "detail": detail})

    # ----------------------------------------------------------------- clients
    def clients(self) -> pd.DataFrame:
        rng, cfg = self.rng, self.p["generation"]
        n = int(cfg["nb_clients"])
        n_pm = int(round(n * float(cfg["part_personnes_morales"])))
        types = np.array(["PP"] * (n - n_pm) + ["PM"] * n_pm)
        rng.shuffle(types)

        lignes, noms_pm = [], set()
        prof_poids = [x[4] for x in PROFESSIONS]
        sect_poids = [x[4] for x in SECTEURS]
        telephones = rng.choice(40_000_000, size=n, replace=False) + 60_000_000
        adresses = rng.choice(len(QUARTIERS) * 2500, size=n, replace=False)
        for i, type_client in enumerate(types):
            ligne = {
                "id_client": f"CL{i + 1:05d}",
                "type_client": type_client,
                "agence": str(self._choix(list(AGENCES), poids=POIDS_AGENCES)),
                "telephone": " ".join(str(telephones[i])[j : j + 2] for j in range(0, 8, 2)),
                "adresse": f"{QUARTIERS[adresses[i] % len(QUARTIERS)]}, lot {adresses[i] // len(QUARTIERS) + 1}",
                "date_entree_relation": self._date_aleatoire(pd.Timestamp("2008-01-01"), pd.Timestamp("2026-03-31")),
                "ppe": "NON" if type_client == "PP" else pd.NA,
                "ppe_approbation_direction": pd.NA,
            }
            if type_client == "PP":
                sexe = "M" if rng.random() < 0.5 else "F"
                prenom, nom = self._nom_pp(sexe)
                prof = PROFESSIONS[int(self._choix(len(PROFESSIONS), poids=prof_poids))]
                age_jours = int(rng.integers(19 * 365, 75 * 365))
                if prof[0] == "Étudiant(e)":
                    age_jours = int(rng.integers(18 * 365, 27 * 365))
                if prof[0] == "Retraité(e)":
                    age_jours = int(rng.integers(60 * 365, 80 * 365))
                revenu = np.exp(rng.uniform(np.log(prof[1]), np.log(prof[2])))
                piece = str(self._choix(["CNI", "PASSEPORT", "CARTE_CONSULAIRE"], poids=[0.75, 0.2, 0.05]))
                ligne.update(
                    {
                        "nom_complet": f"{prenom} {nom}",
                        "date_naissance": (self.arrete - pd.Timedelta(days=age_jours)).normalize(),
                        "date_creation": pd.NaT,
                        "nationalite": str(self._pays(NATIONALITES)),
                        "profession": prof[0],
                        "secteur_activite": pd.NA,
                        "revenu_mensuel_declare": float(round(revenu / 5_000) * 5_000),
                        "chiffre_affaires_annuel_declare": np.nan,
                        "piece_type": piece,
                        "piece_numero": f"{chr(65 + int(rng.integers(0, 26)))}{int(rng.integers(10**7, 10**8))}",
                        "piece_date_expiration": self.arrete + pd.Timedelta(days=int(rng.integers(30, 9 * 365))),
                        "beneficiaire_effectif_identifie": pd.NA,
                        "_profil": prof[3],
                        "_k": prof[5],
                        "_base": float(round(revenu / 5_000) * 5_000),
                    }
                )
            else:
                sect = SECTEURS[int(self._choix(len(SECTEURS), poids=sect_poids))]
                ca = float(round(np.exp(rng.uniform(np.log(sect[1]), np.log(sect[2]))) / 1e6) * 1e6)
                ligne.update(
                    {
                        "nom_complet": self._nom_pm(sect[0], noms_pm),
                        "date_naissance": pd.NaT,
                        "date_creation": self._date_aleatoire(pd.Timestamp("1995-01-01"), pd.Timestamp("2023-12-31")),
                        "nationalite": pd.NA,
                        "profession": pd.NA,
                        "secteur_activite": sect[0],
                        "revenu_mensuel_declare": np.nan,
                        "chiffre_affaires_annuel_declare": ca,
                        "piece_type": "RCCM",
                        "piece_numero": f"RCCM-{int(rng.integers(1995, 2024))}-B-{int(rng.integers(10000, 99999))}",
                        "piece_date_expiration": pd.NaT,
                        "beneficiaire_effectif_identifie": "OUI",
                        "_profil": sect[3],
                        "_k": 0,
                        "_base": ca / 12,
                    }
                )
            lignes.append(ligne)

        clients = pd.DataFrame(lignes)
        # Classification des risques attribuée par la banque.
        pp = clients["type_client"] == "PP"
        clients["niveau_risque"] = np.where(
            pp,
            self._choix(["FAIBLE", "MOYEN", "ELEVE"], n, [0.75, 0.19, 0.06]),
            self._choix(["FAIBLE", "MOYEN", "ELEVE"], n, [0.45, 0.40, 0.15]),
        )
        clients["date_derniere_revue_kyc"] = pd.NaT
        clients["date_dernier_filtrage"] = self.arrete - pd.Timedelta(days=1)
        clients["resultat_dernier_filtrage"] = "AUCUNE_CORRESPONDANCE"
        clients = self._ppe(clients)
        clients["date_derniere_revue_kyc"] = self._revues_conformes(clients)
        # Ménages : 15 paires de clients partageant la même adresse (situation normale).
        paires = self.rng.choice(clients.index[pp], size=30, replace=False).reshape(15, 2)
        for a, b in paires:
            clients.loc[b, "adresse"] = clients.loc[a, "adresse"]
        return clients

    def _ppe(self, clients: pd.DataFrame) -> pd.DataFrame:
        """Désigne les personnes politiquement exposées (PPE), classées à risque élevé."""
        eligibles = clients.index[
            clients["profession"].isin(["Fonctionnaire", "Cadre du secteur privé", "Profession libérale"])
        ]
        ppe = self.rng.choice(eligibles, size=20, replace=False)
        clients.loc[ppe, "ppe"] = "OUI"
        clients.loc[ppe, "ppe_approbation_direction"] = "OUI"
        clients.loc[ppe, "niveau_risque"] = "ELEVE"
        return clients

    def _revues_conformes(self, clients: pd.DataFrame) -> pd.Series:
        """Dates de dernière revue KYC respectant la périodicité de la procédure."""
        periodicite = self.p.hypotheses["revue_kyc_annees"]
        jours_max = clients["niveau_risque"].map(lambda r: int(periodicite[r]) * 365 - 20)
        recul = pd.to_timedelta((self.rng.random(len(clients)) * jours_max).astype(int), unit="D")
        revue = self.arrete - recul
        return revue.where(revue >= clients["date_entree_relation"], clients["date_entree_relation"])

    # ------------------------------------------------------------------ comptes
    def comptes(self, clients: pd.DataFrame) -> pd.DataFrame:
        rng, lignes = self.rng, []
        for _, c in clients.iterrows():
            lignes.append(
                {
                    "id_client": c["id_client"],
                    "type_compte": "COURANT",
                    "agence": c["agence"],
                    "date_ouverture": c["date_entree_relation"],
                }
            )
            if c["type_client"] == "PP" and rng.random() < 0.2:
                ouverture = self._date_aleatoire(c["date_entree_relation"], self.arrete)
                lignes.append(
                    {
                        "id_client": c["id_client"],
                        "type_compte": "EPARGNE",
                        "agence": c["agence"],
                        "date_ouverture": ouverture,
                    }
                )
        comptes = pd.DataFrame(lignes)
        comptes.insert(0, "id_compte", [f"CP{i + 1:06d}" for i in range(len(comptes))])
        comptes["devise"] = "XOF"
        recul = pd.to_timedelta(rng.integers(1, 46, len(comptes)), unit="D")
        dernier = self.debut - recul
        comptes["date_dernier_mouvement_avant_periode"] = dernier.where(dernier >= comptes["date_ouverture"])
        return comptes

    # ---------------------------------------------------------- rôles (injections)
    def roles(self, clients: pd.DataFrame) -> dict[str, list[str]]:
        """Réserve des clients distincts pour chaque typologie injectée."""
        pris: set[str] = set(clients.loc[clients["ppe"] == "OUI", "id_client"])

        def tirer(masque: pd.Series, n: int) -> list[str]:
            candidats = sorted(set(clients.loc[masque, "id_client"]) - pris)
            choisis = [str(x) for x in self.rng.choice(candidats, size=n, replace=False)]
            pris.update(choisis)
            return choisis

        pp = clients["type_client"] == "PP"
        profil = clients["_profil"]
        ancien = clients["date_entree_relation"] < pd.Timestamp("2020-01-01")
        return {
            "fractionnement": tirer(pp & (profil == "especes"), 6) + tirer(pp & (profil == "faible"), 4),
            "compte_de_passage": tirer(pp & profil.isin(["salarie", "faible", "mixte"]), 8),
            "reseau_1": tirer(pp & (profil == "faible"), 5),
            "reseau_2": tirer(pp & profil.isin(["faible", "especes"]), 5),
            "incoherence_profil": tirer(pp & (profil == "faible"), 4)
            + tirer(pp & (profil == "salarie") & (clients["_base"] <= 600_000), 4),
            "reactivation": tirer(pp & ancien, 6),
            "dormants_normaux": tirer(pp & ancien, 40),
            "pays_a_risque": tirer(profil == "pm_international", 4) + tirer(pp & (profil == "especes"), 3),
            "sanctions": tirer(pp & (profil == "salarie"), 3) + tirer(profil == "pm_especes", 1),
            "legitime_profil": tirer(pp & (profil == "salarie") & clients["_base"].between(300_000, 1_500_000), 3),
            "legitime_saisonnier": tirer(profil == "pm_especes", 1),
            "foyer": tirer(pp & (profil == "salarie"), 3),
            "kyc": tirer(pd.Series(True, index=clients.index), 230),
        }

    # ------------------------------------------------- opérations « normales »
    def operations_normales(self, clients: pd.DataFrame, comptes: pd.DataFrame, exclus: set[str]) -> pd.DataFrame:
        """Activité courante, tirée mois par mois selon le profil de chaque client."""
        rng = self.rng
        mois = pd.date_range(self.debut, periods=12, freq="MS")
        nb_jours = mois.days_in_month.to_numpy()
        courant = comptes[comptes["type_compte"] == "COURANT"].set_index("id_client")["id_compte"]
        actifs = clients[~clients["id_client"].isin(exclus)].reset_index(drop=True)
        diaspora = (actifs["type_client"] == "PP").to_numpy() & (rng.random(len(actifs)) < 0.12)
        contreparties = self._pool_contreparties()

        morceaux = []
        for profil, specs in SPECS.items():
            idx_profil = np.flatnonzero(actifs["_profil"].to_numpy() == profil)
            if idx_profil.size == 0:
                continue
            for type_op, intensite, loi in specs:
                lam = (
                    actifs["_k"].to_numpy(float)[idx_profil]
                    if intensite == "k"
                    else np.full(idx_profil.size, intensite)
                )
                if type_op == "SALAIRE":
                    nb = np.ones((idx_profil.size, 12), dtype=int)
                else:
                    nb = rng.poisson(lam[:, None], size=(idx_profil.size, 12))
                morceaux.append(self._tirer(actifs, idx_profil, nb, type_op, loi, lam, nb_jours, mois))
        # Transferts reçus de la diaspora
        idx_d = np.flatnonzero(diaspora)
        nb = rng.poisson(0.5, size=(idx_d.size, 12))
        morceaux.append(
            self._tirer(
                actifs,
                idx_d,
                nb,
                "TRANSFERT_INT_RECU",
                ("u", 0.2, 1.0),
                np.full(idx_d.size, 0.5),
                nb_jours,
                mois,
                pool=POOL_DIASPORA,
            )
        )

        ops = pd.concat(morceaux, ignore_index=True)
        ops["id_compte"] = ops["id_client"].map(courant)
        # Contreparties des virements domestiques
        domestique = ops["type_operation"].isin(["VIREMENT_RECU", "VIREMENT_EMIS"]) & ops["contrepartie"].isna()
        ops.loc[domestique, "contrepartie"] = self._choix(contreparties, int(domestique.sum()))
        # Pas d'opération avant l'ouverture du compte
        ouverture = ops["id_compte"].map(comptes.set_index("id_compte")["date_ouverture"])
        return ops[ops["date_operation"] >= ouverture].reset_index(drop=True)

    def _tirer(self, actifs, idx, nb, type_op, loi, lam, nb_jours, mois, pool=None) -> pd.DataFrame:
        rng = self.rng
        lignes_client = np.repeat(idx, nb.sum(axis=1))
        mois_op = np.concatenate([np.repeat(np.arange(12), ligne) for ligne in nb]) if nb.size else np.array([], int)
        n = lignes_client.size
        base = actifs["_base"].to_numpy(float)[lignes_client]
        if loi[0] == "u":
            facteur = rng.uniform(loi[1], loi[2], n)
        elif loi[0] == "ln":
            facteur = loi[1] * rng.lognormal(0.0, loi[2], n)
        else:  # ln_k : le montant mensuel se répartit sur k versements
            k = np.maximum(lam[np.searchsorted(idx, lignes_client)], 1)
            facteur = loi[1] / k * rng.lognormal(0.0, loi[2], n)
        montant = base * facteur

        type_reel = "VIREMENT_RECU" if type_op == "SALAIRE" else type_op
        if type_op == "SALAIRE":
            jour = rng.integers(24, 28, n)
        else:
            jour = (rng.random(n) * nb_jours[mois_op]).astype(int)
        canal = self._canaux(type_reel, montant)
        h_min = np.array([HEURES[c][0] for c in canal])
        h_max = np.array([HEURES[c][1] for c in canal])
        secondes = ((h_min + rng.random(n) * (h_max - h_min + 1)) * 3600).astype(int)
        dates = (
            mois.to_numpy()[mois_op]
            + pd.to_timedelta(jour, unit="D").to_numpy()
            + pd.to_timedelta(secondes, unit="s").to_numpy()
        )

        agence_client = actifs["agence"].to_numpy()[lignes_client]
        autre_agence = self._choix(list(AGENCES), n, POIDS_AGENCES)
        proba_client = np.where(canal == "GAB", 0.7, np.where(canal == "GUICHET", 0.9, 1.0))
        agence = np.where(rng.random(n) < proba_client, agence_client, autre_agence)

        pays = np.full(n, None, dtype=object)
        contrepartie = np.full(n, None, dtype=object)
        if type_reel.startswith("TRANSFERT"):
            pays_pool = pool or POOL_COMMERCE
            pays = self._pays(pays_pool, n)
            contrepartie = np.array(
                [f"CONTREPARTIE {p} {int(x):03d}" for p, x in zip(pays, rng.integers(1, 60, n))], dtype=object
            )
        if type_op == "SALAIRE":
            prof = actifs["profession"].to_numpy()[lignes_client]
            contrepartie = np.where(
                np.isin(prof, ["Fonctionnaire", "Enseignant(e)"]),
                "TRESOR PUBLIC",
                np.where(prof == "Retraité(e)", "CAISSE NATIONALE DE RETRAITE", None),
            )
        return pd.DataFrame(
            {
                "id_client": actifs["id_client"].to_numpy()[lignes_client],
                "date_operation": dates,
                "type_operation": type_reel,
                "sens": SENS[type_reel],
                "montant": self._arrondir(montant, type_reel),
                "canal": canal,
                "agence_operation": agence,
                "pays_contrepartie": pays,
                "contrepartie": contrepartie,
                "libelle": "Salaire / pension" if type_op == "SALAIRE" else None,
            }
        )

    def _canaux(self, type_op: str, montant: np.ndarray) -> np.ndarray:
        n = montant.size
        if type_op == "VERSEMENT_ESPECES":
            return np.full(n, "GUICHET")
        if type_op == "RETRAIT_ESPECES":
            return np.where((montant <= 300_000) & (self.rng.random(n) < 0.75), "GAB", "GUICHET")
        if type_op == "VIREMENT_RECU":
            return np.full(n, "VIREMENT")
        if type_op == "VIREMENT_EMIS":
            return np.where(self.rng.random(n) < 0.6, "BANQUE_DIGITALE", "GUICHET")
        return np.full(n, "SWIFT")

    @staticmethod
    def _arrondir(montant, type_op: str):
        pas = 5_000 if type_op in ("VERSEMENT_ESPECES", "RETRAIT_ESPECES") else 100
        return (np.maximum(np.round(np.asarray(montant, float) / pas), 1) * pas).astype(np.int64)

    def _pool_contreparties(self) -> list[str]:
        noms, deja = [], set()
        for _ in range(160):
            prenom, nom = self._nom_pp(str(self._choix(["M", "F"])))
            noms.append(f"{prenom} {nom}")
        for _ in range(140):
            noms.append(self._nom_pm(str(self._choix([s[0] for s in SECTEURS])), deja))
        return noms

    # -------------------------------------------------------------- injections
    def _ajouter(
        self,
        client: pd.Series,
        jour: pd.Timestamp,
        type_op: str,
        montant: float,
        *,
        compte: str,
        canal: str | None = None,
        agence: str | None = None,
        pays: str | None = None,
        contrepartie: str | None = None,
        libelle: str | None = None,
    ) -> None:
        canal = canal or str(self._canaux(type_op, np.array([montant]))[0])
        self.ops_injectees.append(
            {
                "id_client": client["id_client"],
                "id_compte": compte,
                "date_operation": self._heure(jour, canal),
                "type_operation": type_op,
                "sens": SENS[type_op],
                "montant": int(self._arrondir([montant], type_op)[0]),
                "canal": canal,
                "agence_operation": agence or client["agence"],
                "pays_contrepartie": pays,
                "contrepartie": contrepartie,
                "libelle": libelle,
            }
        )

    def _debuts_episodes(self, nb: int, ecart_min: int = 20, marge_fin: int = 15) -> list[pd.Timestamp]:
        """Dates de début d'épisodes espacées d'au moins `ecart_min` jours."""
        fenetre = (self.fin - self.debut).days - marge_fin
        for _ in range(200):
            jours = np.sort(self.rng.choice(fenetre, size=nb, replace=False))
            if nb == 1 or np.diff(jours).min() >= ecart_min:
                return [self.debut + pd.Timedelta(days=int(j)) for j in jours]
        return [self.debut + pd.Timedelta(days=int(j)) for j in np.linspace(0, fenetre, nb)]

    def injecter(self, clients: pd.DataFrame, comptes: pd.DataFrame, roles: dict[str, list[str]]) -> None:
        idx = clients.set_index("id_client")
        courant = comptes[comptes["type_compte"] == "COURANT"].set_index("id_client")["id_compte"]
        rng, S = self.rng, self.seuil_dte

        def client(id_client: str) -> pd.Series:
            ligne = idx.loc[id_client].copy()
            ligne["id_client"] = id_client
            return ligne

        # 1. Fractionnement des versements d'espèces sous le seuil de déclaration
        bande = float(self.p.hypotheses["fractionnement"]["bande_basse"])
        for cid in roles["fractionnement"]:
            c, total_client = client(cid), 0
            for debut in self._debuts_episodes(int(rng.integers(2, 5)), ecart_min=35):
                k = int(rng.integers(3, 5))
                jours = np.sort(rng.choice(6, size=k, replace=False))
                agences = self._choix(list(AGENCES), k)
                cumul = 0
                for j, ag in zip(jours, agences):
                    montant = round(rng.uniform(max(bande, 0.72), 0.99) * S / 50_000) * 50_000
                    cumul += montant
                    self._ajouter(
                        c,
                        debut + pd.Timedelta(days=int(j)),
                        "VERSEMENT_ESPECES",
                        montant,
                        compte=courant[cid],
                        agence=str(ag),
                        libelle="Versement espèces",
                    )
                total_client += cumul
                if rng.random() < 0.7:  # sortie des fonds, elle aussi fractionnée
                    for part in rng.dirichlet(np.ones(int(rng.integers(2, 4)))) * cumul * rng.uniform(0.8, 0.95):
                        sortie = str(self._choix(["TRANSFERT_INT_EMIS", "VIREMENT_EMIS"]))
                        pays = str(self._choix(["AE", "CN", "TR"])) if sortie.startswith("TRANSFERT") else None
                        self._ajouter(
                            c,
                            debut + pd.Timedelta(days=int(rng.integers(7, 15))),
                            sortie,
                            part,
                            compte=courant[cid],
                            pays=pays,
                            contrepartie=f"CONTREPARTIE {pays} 777" if pays else "SAVANE EXPRESS SERVICES SARL",
                        )
            self._verite(cid, "FRACTIONNEMENT", f"Versements espèces sous le seuil : {total_client:,.0f} FCFA")

        # 2. Comptes de passage : crédits importants ressortis sous 48 heures
        for cid in roles["compte_de_passage"]:
            c = client(cid)
            nb_ep = int(rng.integers(4, 8))
            for debut in self._debuts_episodes(nb_ep, ecart_min=15):
                montant = round(rng.uniform(10.5e6, 35e6) / 100_000) * 100_000
                entree = str(
                    self._choix(["VIREMENT_RECU", "TRANSFERT_INT_RECU", "VERSEMENT_ESPECES"], poids=[0.55, 0.3, 0.15])
                )
                pays = str(self._choix(["AE", "CN", "FR", "TR", "GH"])) if entree.startswith("TRANSFERT") else None
                self._ajouter(
                    c,
                    debut,
                    entree,
                    montant,
                    compte=courant[cid],
                    pays=pays,
                    contrepartie=f"CONTREPARTIE {pays} 555" if pays else None,
                )
                n_sorties = int(rng.integers(1, 4))
                parts = rng.dirichlet(np.ones(n_sorties)) * montant * rng.uniform(0.92, 1.0)
                for part in parts:
                    sortie = str(
                        self._choix(["RETRAIT_ESPECES", "VIREMENT_EMIS", "TRANSFERT_INT_EMIS"], poids=[0.4, 0.35, 0.25])
                    )
                    pays_s = str(self._choix(["AE", "CN", "TR"])) if sortie.startswith("TRANSFERT") else None
                    self._ajouter(
                        c,
                        debut + pd.Timedelta(days=int(rng.integers(0, 3))),
                        sortie,
                        part,
                        compte=courant[cid],
                        canal="GUICHET" if sortie == "RETRAIT_ESPECES" else None,
                        pays=pays_s,
                        contrepartie=f"CONTREPARTIE {pays_s} 556" if pays_s else None,
                    )
            self._verite(cid, "COMPTE_DE_PASSAGE", f"{nb_ep} épisodes de transit rapide")

        # 3. Réseaux de prête-noms : identifiants partagés, fonds collectés puis envoyés à un même bénéficiaire
        for groupe, (agence, beneficiaire, pays, partage) in {
            "reseau_1": ("AG04", "ZENTRA GLOBAL SERVICES FZE", "AE", "telephone"),
            "reseau_2": ("AG02", "SAVANE EXPRESS SERVICES SARL", None, "adresse"),
        }.items():
            membres = roles[groupe]
            entree = self._date_aleatoire(pd.Timestamp("2025-03-01"), pd.Timestamp("2025-04-30"))
            for i, cid in enumerate(membres):
                ligne = clients.index[clients["id_client"] == cid][0]
                clients.loc[ligne, "agence"] = agence
                clients.loc[ligne, "date_entree_relation"] = entree + pd.Timedelta(days=int(rng.integers(0, 21)))
                clients.loc[ligne, "date_derniere_revue_kyc"] = clients.loc[ligne, "date_entree_relation"]
                if i > 0:
                    ref = clients.index[clients["id_client"] == membres[0]][0]
                    clients.loc[ligne, partage] = clients.loc[ref, partage]
                    if partage == "adresse" and i in (1, 2):
                        clients.loc[ligne, "telephone"] = clients.loc[ref, "telephone"]
                ligne_cpt = comptes.index[comptes["id_client"] == cid]
                comptes.loc[ligne_cpt, "agence"] = agence
                comptes.loc[ligne_cpt, "date_ouverture"] = clients.loc[ligne, "date_entree_relation"]
                comptes.loc[ligne_cpt, "date_dernier_mouvement_avant_periode"] = pd.NaT
                c = client(cid)
                c["agence"] = agence
                for debut in self._debuts_episodes(int(rng.integers(3, 7)), ecart_min=25):
                    montant = round(rng.uniform(2e6, 6e6) / 50_000) * 50_000
                    self._ajouter(
                        c,
                        debut,
                        "VERSEMENT_ESPECES",
                        montant,
                        compte=courant[cid],
                        libelle="Versement espèces (déposant tiers)",
                    )
                    sortie = "TRANSFERT_INT_EMIS" if pays else "VIREMENT_EMIS"
                    self._ajouter(
                        c,
                        debut + pd.Timedelta(days=int(rng.integers(1, 6))),
                        sortie,
                        montant * rng.uniform(0.85, 0.95),
                        compte=courant[cid],
                        pays=pays,
                        contrepartie=beneficiaire,
                    )
                self._verite(cid, "RESEAU", f"{groupe} : {partage} partagé, fonds vers {beneficiaire}")

        # 4. Flux sans rapport avec le profil déclaré
        for cid in roles["incoherence_profil"]:
            c = client(cid)
            mois = self.rng.choice(12, size=int(rng.integers(2, 6)), replace=False)
            for m in sorted(mois):
                debut_mois = self.debut + pd.DateOffset(months=int(m))
                for _ in range(int(rng.integers(1, 3))):
                    jour = debut_mois + pd.Timedelta(days=int(rng.integers(0, 25)))
                    entree = str(self._choix(["VIREMENT_RECU", "TRANSFERT_INT_RECU"], poids=[0.6, 0.4]))
                    pays = str(self._choix(["FR", "US", "AE", "CN"])) if entree.startswith("TRANSFERT") else None
                    montant = round(rng.uniform(6e6, 25e6) / 100_000) * 100_000
                    self._ajouter(
                        c,
                        jour,
                        entree,
                        montant,
                        compte=courant[cid],
                        pays=pays,
                        contrepartie=f"CONTREPARTIE {pays} 321" if pays else None,
                    )
                    for _ in range(int(rng.integers(1, 4))):
                        self._ajouter(
                            c,
                            jour + pd.Timedelta(days=int(rng.integers(3, 25))),
                            "RETRAIT_ESPECES",
                            montant * rng.uniform(0.1, 0.25),
                            compte=courant[cid],
                            canal="GUICHET",
                        )
            self._verite(cid, "INCOHERENCE_PROFIL", "Crédits sans rapport avec le revenu déclaré")

        # 5. Comptes inactifs réactivés puis vidés
        for cid in roles["reactivation"] + roles["dormants_normaux"]:
            ligne_cpt = comptes.index[(comptes["id_client"] == cid) & (comptes["type_compte"] == "COURANT")]
            dernier = self._date_aleatoire(pd.Timestamp("2021-01-01"), pd.Timestamp("2024-05-31"))
            comptes.loc[ligne_cpt, "date_dernier_mouvement_avant_periode"] = dernier
        for cid in roles["reactivation"]:
            c = client(cid)
            jour = self._date_aleatoire(self.debut + pd.Timedelta(days=30), self.fin - pd.Timedelta(days=30))
            montant = round(rng.uniform(8e6, 30e6) / 100_000) * 100_000
            entree = str(self._choix(["VERSEMENT_ESPECES", "VIREMENT_RECU"]))
            agence = str(self._choix(list(AGENCES)))
            self._ajouter(c, jour, entree, montant, compte=courant[cid], agence=agence)
            parts = rng.dirichlet(np.ones(int(rng.integers(1, 4)))) * montant * rng.uniform(0.85, 0.98)
            for part in parts:
                sortie = str(self._choix(["RETRAIT_ESPECES", "VIREMENT_EMIS"]))
                self._ajouter(
                    c,
                    jour + pd.Timedelta(days=int(rng.integers(1, 11))),
                    sortie,
                    part,
                    compte=courant[cid],
                    canal="GUICHET" if sortie == "RETRAIT_ESPECES" else None,
                    agence=agence,
                )
            self._verite(cid, "REACTIVATION_DORMANT", f"Compte inactif réactivé : {montant:,.0f} FCFA")
        for cid in roles["dormants_normaux"][:8]:  # petites réactivations sans enjeu
            c = client(cid)
            jour = self._date_aleatoire(self.debut, self.fin - pd.Timedelta(days=10))
            for _ in range(int(rng.integers(1, 4))):
                self._ajouter(
                    c,
                    jour + pd.Timedelta(days=int(rng.integers(0, 10))),
                    "VERSEMENT_ESPECES",
                    rng.uniform(20_000, 300_000),
                    compte=courant[cid],
                )

        # 6. Flux avec des pays sous surveillance du GAFI
        destinations = ["LB", "LB", "LB", "AO", "IQ", "MM", "SY"]
        for cid, pays in zip(roles["pays_a_risque"], destinations):
            c = client(cid)
            for debut in self._debuts_episodes(int(rng.integers(2, 6)), ecart_min=20):
                sens = "TRANSFERT_INT_EMIS" if rng.random() < 0.75 else "TRANSFERT_INT_RECU"
                self._ajouter(
                    c,
                    debut,
                    sens,
                    round(rng.uniform(5e6, 45e6) / 100_000) * 100_000,
                    compte=courant[cid],
                    pays=pays,
                    contrepartie=f"CONTREPARTIE {pays} 900",
                )
            self._verite(cid, "PAYS_A_RISQUE", f"Transferts avec {pays}")
        faibles = roles["pays_a_risque"][:3]
        clients.loc[clients["id_client"].isin(faibles), "niveau_risque"] = "FAIBLE"

        # 7. Situations atypiques mais légitimes : faux positifs attendus, à lever sur pièces
        motifs = [
            ("ETUDE NOTARIALE DU CENTRE", "Produit de cession d'un terrain (acte notarié)"),
            ("CAISSE NATIONALE DE RETRAITE", "Indemnité de départ à la retraite"),
            ("COMPAGNIE D'ASSURANCES DU SAHEL", "Indemnisation d'un sinistre"),
        ]
        for cid, (contrepartie, libelle) in zip(roles["legitime_profil"], motifs):
            c = client(cid)
            for m in sorted(rng.choice(12, size=2, replace=False)):
                jour = self.debut + pd.DateOffset(months=int(m)) + pd.Timedelta(days=int(rng.integers(2, 20)))
                self._ajouter(
                    c,
                    jour,
                    "VIREMENT_RECU",
                    round(rng.uniform(12e6, 30e6) / 100_000) * 100_000,
                    compte=courant[cid],
                    contrepartie=contrepartie,
                    libelle=libelle,
                )
            self._verite(cid, "FAUX_POSITIF", f"{libelle} : justificatif disponible")
        cid = roles["legitime_saisonnier"][0]
        c, debut = client(cid), pd.Timestamp("2025-12-18")
        for j in np.sort(rng.choice(6, size=4, replace=False)):
            self._ajouter(
                c,
                debut + pd.Timedelta(days=int(j)),
                "VERSEMENT_ESPECES",
                round(rng.uniform(0.75, 0.97) * S / 50_000) * 50_000,
                compte=courant[cid],
                libelle="Versement recettes",
            )
        self._verite(cid, "FAUX_POSITIF", "Recettes de fin d'année cohérentes avec le chiffre d'affaires")
        cid = roles["dormants_normaux"][8]
        c = client(cid)
        jour = self._date_aleatoire(self.debut + pd.Timedelta(days=60), self.fin - pd.Timedelta(days=60))
        self._ajouter(
            c,
            jour,
            "VIREMENT_RECU",
            round(rng.uniform(6e6, 9e6) / 100_000) * 100_000,
            compte=courant[cid],
            contrepartie="CAISSE NATIONALE DE RETRAITE",
            libelle="Rappel de pension (arriérés)",
        )
        for k in range(4):
            self._ajouter(
                c,
                jour + pd.Timedelta(days=12 + 25 * k),
                "RETRAIT_ESPECES",
                rng.uniform(300_000, 900_000),
                compte=courant[cid],
                canal="GUICHET",
            )
        self._verite(cid, "FAUX_POSITIF", "Réactivation par un rappel de pension documenté")
        foyer = roles["foyer"]
        ref = clients.index[clients["id_client"] == foyer[0]][0]
        nom_famille = clients.loc[ref, "nom_complet"].split(" ", 1)[1]
        for cid in foyer:
            ligne = clients.index[clients["id_client"] == cid][0]
            clients.loc[ligne, "adresse"] = clients.loc[ref, "adresse"]
            prenom = clients.loc[ligne, "nom_complet"].split(" ", 1)[0]
            clients.loc[ligne, "nom_complet"] = f"{prenom} {nom_famille}"
            self._verite(cid, "FAUX_POSITIF", "Membres d'un même foyer (justificatif de domicile)")

    # ------------------------------------------------------------- assemblage
    def assembler(self, normales: pd.DataFrame) -> pd.DataFrame:
        injectees = pd.DataFrame(self.ops_injectees)
        injectees["date_operation"] = pd.to_datetime(injectees["date_operation"])
        ops = pd.concat([normales, injectees], ignore_index=True)
        fin_journee = self.fin + pd.Timedelta(hours=23, minutes=59, seconds=59)
        ops = ops[(ops["date_operation"] >= self.debut) & (ops["date_operation"] <= fin_journee)]
        ops = ops.sort_values(["date_operation", "id_client"], kind="stable").reset_index(drop=True)
        libelles = {
            "VERSEMENT_ESPECES": "Versement espèces",
            "RETRAIT_ESPECES": "Retrait espèces",
            "VIREMENT_RECU": "Virement reçu",
            "VIREMENT_EMIS": "Virement émis",
            "TRANSFERT_INT_RECU": "Transfert international reçu",
            "TRANSFERT_INT_EMIS": "Transfert international émis",
        }
        ops["libelle"] = ops["libelle"].fillna(ops["type_operation"].map(libelles))
        ops.loc[(ops["type_operation"] == "RETRAIT_ESPECES") & (ops["canal"] == "GAB"), "libelle"] = "Retrait GAB"
        ops.insert(0, "id_operation", [f"OP{i + 1:07d}" for i in range(len(ops))])
        colonnes = [
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
        ]
        return ops[colonnes]

    # ---------------------------------------------------------- anomalies KYC
    def anomalies_kyc(self, clients: pd.DataFrame, roles: dict[str, list[str]]) -> pd.DataFrame:
        rng = self.rng
        reserve = list(roles["kyc"])
        rng.shuffle(reserve)
        periodicite = self.p.hypotheses["revue_kyc_annees"]

        # Données obligatoires manquantes (concentrées à l'agence AG03)
        candidats_ag03 = [c for c in reserve if clients.loc[clients["id_client"] == c, "agence"].iloc[0] == "AG03"]
        autres = [c for c in reserve if c not in candidats_ag03]
        incomplets = candidats_ag03[:33] + autres[:22]
        for cid in incomplets:
            ligne = clients.index[clients["id_client"] == cid][0]
            pm = clients.loc[ligne, "type_client"] == "PM"
            champs = [
                "secteur_activite" if pm else "profession",
                "chiffre_affaires_annuel_declare" if pm else "revenu_mensuel_declare",
                "adresse",
                "piece_numero",
            ]
            for champ in rng.choice(champs, size=int(rng.integers(1, 3)), replace=False):
                clients.loc[ligne, champ] = np.nan if "declare" in champ else pd.NA
        reste = [c for c in reserve if c not in incomplets]

        # Pièces d'identité expirées (personnes physiques)
        pp_reste = [c for c in reste if clients.loc[clients["id_client"] == c, "type_client"].iloc[0] == "PP"]
        expirees = pp_reste[:40]
        for cid in expirees:
            clients.loc[clients["id_client"] == cid, "piece_date_expiration"] = self.arrete - pd.Timedelta(
                days=int(rng.integers(10, 900))
            )
        reste = [c for c in reste if c not in expirees]

        # Revues KYC périodiques en retard
        en_retard = reste[:60]
        for cid in en_retard:
            ligne = clients.index[clients["id_client"] == cid][0]
            annees = int(periodicite[clients.loc[ligne, "niveau_risque"]])
            retard = self.arrete - pd.Timedelta(days=annees * 365 + int(rng.integers(30, 700)))
            clients.loc[ligne, "date_derniere_revue_kyc"] = retard
            if clients.loc[ligne, "date_entree_relation"] > retard:
                clients.loc[ligne, "date_entree_relation"] = retard - pd.Timedelta(days=int(rng.integers(30, 900)))
        reste = [c for c in reste if c not in en_retard]

        # Personnes morales sans bénéficiaire effectif identifié
        pm_reste = [c for c in reste if clients.loc[clients["id_client"] == c, "type_client"].iloc[0] == "PM"]
        pm_tous = clients.loc[(clients["type_client"] == "PM") & clients["id_client"].isin(reste), "id_client"]
        sans_be = (pm_reste + [c for c in pm_tous if c not in pm_reste])[:16]
        clients.loc[clients["id_client"].isin(sans_be), "beneficiaire_effectif_identifie"] = "NON"
        clients.loc[clients["id_client"].isin(sans_be[:6]), "niveau_risque"] = "FAIBLE"

        # PPE : approbation manquante, classification incohérente, réévaluation dépassée
        ppe = clients.loc[clients["ppe"] == "OUI", "id_client"].tolist()
        sans_approbation, mal_classees, revue_depassee = ppe[:6], ppe[6:10], ppe[10:13]
        clients.loc[clients["id_client"].isin(sans_approbation[:4]), "ppe_approbation_direction"] = "NON"
        clients.loc[clients["id_client"].isin(sans_approbation[4:]), "ppe_approbation_direction"] = pd.NA
        clients.loc[clients["id_client"].isin(mal_classees[:2]), "niveau_risque"] = "FAIBLE"
        clients.loc[clients["id_client"].isin(mal_classees[2:]), "niveau_risque"] = "MOYEN"
        for cid in revue_depassee:
            ligne = clients.index[clients["id_client"] == cid][0]
            clients.loc[ligne, "date_derniere_revue_kyc"] = self.arrete - pd.Timedelta(
                days=int(rng.integers(int(3.2 * 365), 5 * 365))
            )
            clients.loc[ligne, "date_entree_relation"] = min(
                clients.loc[ligne, "date_entree_relation"], pd.Timestamp("2018-01-01")
            )

        self.meta.update(
            {
                "kyc_incomplets": sorted(incomplets),
                "pieces_expirees": sorted(expirees),
                "revues_en_retard": sorted(en_retard),
                "pm_sans_be": sorted(sans_be),
                "ppe": sorted(ppe),
                "ppe_sans_approbation": sorted(sans_approbation),
                "ppe_mal_classees": sorted(mal_classees),
                "ppe_revue_depassee": sorted(revue_depassee),
            }
        )
        return clients

    # ---------------------------------------------------------- liste de sanctions
    def liste_sanctions(self, clients: pd.DataFrame, roles: dict[str, list[str]]) -> pd.DataFrame:
        lignes = []
        for i, (prenom, nom, naissance) in enumerate(SANCTIONS_PP, start=1):
            lignes.append(
                {
                    "id_entree": f"FICT-{i:03d}",
                    "nom": f"{nom} {prenom}",
                    "type_entite": "PP",
                    "date_naissance": pd.Timestamp(naissance),
                    "programme": "LISTE FICTIVE DE DEMONSTRATION",
                }
            )
        for j, nom in enumerate(SANCTIONS_PM, start=len(lignes) + 1):
            lignes.append(
                {
                    "id_entree": f"FICT-{j:03d}",
                    "nom": nom,
                    "type_entite": "PM",
                    "date_naissance": pd.NaT,
                    "programme": "LISTE FICTIVE DE DEMONSTRATION",
                }
            )
        liste = pd.DataFrame(lignes)
        liste["date_inscription"] = [
            self._date_aleatoire(pd.Timestamp("2016-01-01"), pd.Timestamp("2026-03-31")) for _ in range(len(liste))
        ]

        # Clients dont l'identité correspond (ou ressemble) à une entrée de la liste
        pp1, pp2, pp3, pm1 = roles["sanctions"]
        corrections = {
            pp1: ("Seydou KANTÉ", "1979-11-04", "SANCTIONS_CORRESPONDANCE", "FICT-016 : nom inversé, accent"),
            pp2: ("Mahamane DJIBRILLA", "1983-02-17", "SANCTIONS_CORRESPONDANCE", "FICT-015 : orthographe voisine"),
            pp3: (
                "Aminata SANGARÉ",
                "1994-05-12",
                "SANCTIONS_HOMONYME",
                "FICT-017 : même nom, autre date de naissance",
            ),
        }
        for cid, (nom, naissance, typologie, detail) in corrections.items():
            clients.loc[clients["id_client"] == cid, ["nom_complet", "date_naissance"]] = [nom, pd.Timestamp(naissance)]
            self._verite(cid, typologie, detail)
        clients.loc[clients["id_client"] == pm1, "nom_complet"] = "KORALIS NÉGOCE SARL"
        self._verite(pm1, "SANCTIONS_CORRESPONDANCE", "FICT-029 : même raison sociale, forme juridique ajoutée")
        return liste[["id_entree", "nom", "type_entite", "date_naissance", "programme", "date_inscription"]]

    # ------------------------------------------------------ alertes de la banque
    def alertes_banque(self, ops: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
        """Rejoue les trois scénarios paramétrés dans l'outil de la banque, puis simule leur traitement."""
        cfg = self.p["parametrage_banque"]
        liste = set(cfg["liste_pays_a_risque"])
        esp = ops[(ops["type_operation"] == "VERSEMENT_ESPECES") & (ops["montant"] >= self.seuil_dte)]
        transferts = ops[ops["type_operation"].str.startswith("TRANSFERT")]
        pay = transferts[transferts["pays_contrepartie"].isin(liste)]
        trf = transferts[
            ~transferts["pays_contrepartie"].isin(liste) & (transferts["montant"] >= cfg["trf01_montant_min"])
        ]
        alertes = [
            pd.DataFrame(
                {
                    "id_client": t["id_client"],
                    "id_operation": t["id_operation"],
                    "scenario": code,
                    "date_alerte": t["date_operation"].dt.normalize() + pd.Timedelta(days=1),
                }
            )
            for code, t in (("ESP-01", esp), ("PAY-01", pay), ("TRF-01", trf))
        ]
        credits = ops[ops["sens"] == "C"].assign(mois=ops["date_operation"].dt.to_period("M"))
        mensuel = credits.groupby(["id_client", "mois"], as_index=False)["montant"].sum()
        ref = clients.set_index("id_client")
        base = np.where(
            ref["type_client"] == "PP",
            ref["revenu_mensuel_declare"] * cfg["pro01_multiple_pp"],
            ref["chiffre_affaires_annuel_declare"] / 12 * cfg["pro01_multiple_pm"],
        )
        mensuel["plafond"] = mensuel["id_client"].map(pd.Series(base, index=ref.index))
        pro = mensuel[(mensuel["montant"] >= mensuel["plafond"]) & (mensuel["montant"] >= cfg["pro01_montant_min"])]
        alertes.append(
            pd.DataFrame(
                {
                    "id_client": pro["id_client"],
                    "id_operation": pd.NA,
                    "scenario": "PRO-01",
                    "date_alerte": pro["mois"].dt.to_timestamp(how="end").dt.normalize() + pd.Timedelta(days=1),
                }
            )
        )
        alertes = pd.concat(alertes, ignore_index=True)
        alertes = alertes[alertes["date_alerte"] <= self.arrete].sort_values(["date_alerte", "id_client"])
        alertes = alertes.reset_index(drop=True)
        alertes.insert(0, "id_alerte", [f"AL{i + 1:05d}" for i in range(len(alertes))])
        return self._traitement_alertes(alertes)

    def _traitement_alertes(self, alertes: pd.DataFrame) -> pd.DataFrame:
        rng, n = self.rng, len(alertes)
        alertes["analyste"] = self._choix(ANALYSTES, n, [0.22, 0.26, 0.18, 0.18, 0.16])
        age = (self.arrete - alertes["date_alerte"]).dt.days.to_numpy()
        # Alertes récentes encore ouvertes (normal) ; arriéré injecté sur les plus anciennes
        ouverte = age <= 15
        anciennes = np.flatnonzero(age > 45)
        proba = np.where(alertes["analyste"].to_numpy()[anciennes] == "A02", 0.35, 0.06)
        arriere = anciennes[rng.random(anciennes.size) < proba]
        ouverte[arriere] = True
        duree = np.minimum(np.ceil(rng.gamma(2.0, 4.0, n)), 28).astype(int)
        cloture = alertes["date_alerte"] + pd.to_timedelta(duree, unit="D")
        cloture = cloture.where(cloture <= self.arrete, self.arrete)
        alertes["statut"] = np.where(ouverte, "OUVERTE", "CLOTUREE")
        alertes["date_cloture"] = cloture.where(~ouverte)
        motifs = [
            "Opération cohérente avec l'activité déclarée",
            "Justificatif obtenu (facture / contrat)",
            "Client connu, flux habituel",
            "Origine des fonds documentée",
            "Faux positif du scénario",
        ]
        alertes["motif_cloture"] = np.where(ouverte, None, self._choix(motifs, n))
        alertes["decision"] = np.where(ouverte, "EN_COURS", "CLASSEMENT_SANS_SUITE")

        # Clôtures sans motif
        fermees = np.flatnonzero(~ouverte)
        sans_motif = rng.choice(fermees, size=int(round(0.08 * fermees.size)), replace=False)
        alertes.loc[sans_motif, "motif_cloture"] = None
        # Clôtures en masse par un même analyste en fin d'exercice / de semestre
        massives = []
        for jour, nb in (("2025-12-31", 20), ("2026-06-29", 16)):
            jour = pd.Timestamp(jour)
            fenetre = alertes.index[
                (alertes["date_alerte"] < jour)
                & (alertes["date_alerte"] >= jour - pd.Timedelta(days=75))
                & (alertes["statut"] == "CLOTUREE")
                & ~alertes.index.isin(massives)
            ]
            choix = rng.choice(fenetre, size=min(nb, len(fenetre)), replace=False)
            alertes.loc[choix, ["analyste", "date_cloture", "motif_cloture"]] = ["A04", jour, "Clôture groupée"]
            massives.extend(choix.tolist())
        self.meta.update(
            {
                "alertes_arriere": sorted(alertes.loc[arriere, "id_alerte"]),
                "alertes_sans_motif": sorted(alertes.loc[sans_motif, "id_alerte"]),
                "alertes_clotures_massives": sorted(alertes.loc[massives, "id_alerte"]),
            }
        )
        return alertes[
            [
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
            ]
        ]

    # ------------------------------------------------------ registres déclaratifs
    def declarations_soupcon(self, alertes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        rng = self.rng
        suspects = {v["id_client"] for v in self.verite}
        fermees = alertes[(alertes["statut"] == "CLOTUREE") & (alertes["motif_cloture"] != "Clôture groupée")]
        sur_suspects = fermees[fermees["id_client"].isin(suspects)].drop_duplicates("id_client")
        sur_suspects = sur_suspects.sample(frac=0.6, random_state=int(rng.integers(1_000_000)))
        autres = fermees[~fermees["id_client"].isin(suspects)].drop_duplicates("id_client")
        autres = autres.sample(n=min(10, len(autres)), random_state=int(rng.integers(1_000_000)))
        retenues = pd.concat([sur_suspects, autres]).sort_values("date_alerte")

        lignes = []
        for i, (_, a) in enumerate(retenues.iterrows(), start=1):
            analyse = int(rng.choice([6, 10, 14, 21, 28, 45, 60, 75], p=[0.15, 0.2, 0.2, 0.15, 0.1, 0.1, 0.05, 0.05]))
            decision = min(a["date_alerte"] + pd.Timedelta(days=analyse), self.arrete - pd.Timedelta(days=3))
            transmission = min(
                decision
                + pd.Timedelta(
                    days=int(rng.choice([0, 1, 1, 2, 3, 5, 9, 15], p=[0.25, 0.2, 0.15, 0.1, 0.1, 0.08, 0.07, 0.05]))
                ),
                self.arrete,
            )
            ident = f"DS{i:04d}"
            lignes.append(
                {
                    "id_ds": ident,
                    "id_alerte": a["id_alerte"],
                    "id_client": a["id_client"],
                    "date_alerte": a["date_alerte"],
                    "date_decision": decision,
                    "date_transmission": transmission,
                    "statut": "TRANSMISE",
                }
            )
            alertes.loc[alertes["id_alerte"] == a["id_alerte"], ["decision", "date_cloture", "motif_cloture"]] = [
                "DECLARATION_SOUPCON",
                decision,
                "Déclaration de soupçon transmise à la CENTIF",
            ]
        ds = pd.DataFrame(lignes)
        return ds, alertes

    def declarations_especes(self, ops: pd.DataFrame, clients: pd.DataFrame) -> pd.DataFrame:
        """Registre des déclarations de transactions en espèces (DTE) tenu par la banque."""
        rng = self.rng
        esp = ops[ops["type_operation"].isin(["VERSEMENT_ESPECES", "RETRAIT_ESPECES"])].copy()
        esp["jour"] = esp["date_operation"].dt.normalize()
        agence = esp.groupby(["id_client", "jour", "type_operation"])["agence_operation"].first()
        cumul = esp.groupby(["id_client", "jour", "type_operation"])["montant"].sum()
        attendues = cumul[cumul >= self.seuil_dte].reset_index()
        attendues["agence"] = agence.loc[cumul[cumul >= self.seuil_dte].index].to_numpy()
        proba_oubli = np.where(attendues["agence"] == "AG05", 0.5, 0.1)
        oubli = rng.random(len(attendues)) < proba_oubli
        declarees = attendues[~oubli].reset_index(drop=True)
        delai = pd.to_timedelta(rng.integers(1, 12, len(declarees)), unit="D")
        registre = pd.DataFrame(
            {
                "id_dte": [f"DTE{i + 1:05d}" for i in range(len(declarees))],
                "id_client": declarees["id_client"],
                "date_operation": declarees["jour"],
                "type_operation": declarees["type_operation"],
                "montant_declare": declarees["montant"].astype(np.int64),
                "date_declaration": (declarees["jour"] + delai).where(
                    declarees["jour"] + delai <= self.arrete, self.arrete
                ),
            }
        )
        self.meta["dte_manquantes"] = [
            f"{r.id_client}|{r.jour:%Y-%m-%d}|{r.type_operation}" for r in attendues[oubli].itertuples()
        ]
        return registre

    # ------------------------------------------------------------- finalisation
    def statut_comptes(self, comptes: pd.DataFrame, ops: pd.DataFrame) -> pd.DataFrame:
        dernier = ops.groupby("id_compte")["date_operation"].max()
        mouvement = comptes["id_compte"].map(dernier).fillna(comptes["date_dernier_mouvement_avant_periode"])
        actif = mouvement >= self.arrete - pd.Timedelta(days=365)
        comptes["statut"] = np.where(actif, "ACTIF", "INACTIF")
        return comptes[
            [
                "id_compte",
                "id_client",
                "type_compte",
                "devise",
                "agence",
                "date_ouverture",
                "date_dernier_mouvement_avant_periode",
                "statut",
            ]
        ]

    def executer(self) -> tuple[Donnees, pd.DataFrame, dict]:
        clients = self.clients()
        comptes = self.comptes(clients)
        roles = self.roles(clients)
        exclus = set(roles["reactivation"]) | set(roles["dormants_normaux"])
        normales = self.operations_normales(clients, comptes, exclus)
        self.injecter(clients, comptes, roles)
        ops = self.assembler(normales)
        # Les comptes des réseaux ont été ouverts récemment : pas d'opération avant l'ouverture
        ouverture = ops["id_compte"].map(comptes.set_index("id_compte")["date_ouverture"])
        ops = ops[ops["date_operation"] >= ouverture].reset_index(drop=True)
        clients = self.anomalies_kyc(clients, roles)
        sanctions = self.liste_sanctions(clients, roles)
        alertes = self.alertes_banque(ops, clients)
        ds, alertes = self.declarations_soupcon(alertes)
        dte = self.declarations_especes(ops, clients)
        comptes = self.statut_comptes(comptes, ops)

        colonnes = [
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
        ]
        donnees = Donnees(
            clients=clients[colonnes].copy(),
            comptes=comptes,
            operations=ops,
            alertes=alertes,
            declarations_soupcon=ds,
            declarations_especes=dte,
            liste_sanctions=sanctions,
        )
        verite = pd.DataFrame(self.verite).sort_values(["typologie", "id_client"]).reset_index(drop=True)
        self.meta.update(
            {
                "nb_clients": len(clients),
                "nb_operations": len(ops),
                "nb_alertes": len(alertes),
                "roles": {k: sorted(v) for k, v in roles.items() if k != "kyc"},
            }
        )
        return donnees, verite, self.meta


def generer_donnees(p: Parametres | None = None) -> tuple[Donnees, pd.DataFrame, dict]:
    """Génère le jeu de données fictif ; renvoie (données, vérité terrain, métadonnées)."""
    return _Generateur(p or charger_parametres()).executer()


def ecrire_jeu_de_donnees(p: Parametres | None = None, dossier: str | Path | None = None) -> Path:
    """Génère puis écrit le jeu de données (CSV) dans `dossier` (par défaut data/synthetiques)."""
    p = p or charger_parametres()
    dossier = Path(dossier) if dossier else p.dossier_donnees
    donnees, verite, meta = generer_donnees(p)
    sauvegarder_donnees(donnees, dossier)
    ecrire_table(verite, dossier / "verite_terrain.csv")
    with open(dossier / "metadonnees_generation.json", "w", encoding="utf-8") as fichier:
        json.dump(meta, fichier, ensure_ascii=False, indent=2, default=str)
    return dossier
