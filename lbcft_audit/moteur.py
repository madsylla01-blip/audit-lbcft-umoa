"""Exécution de l'ensemble des tests, mesure de couverture du dispositif et priorisation des clients."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .donnees import Donnees, charger_donnees
from .integrite import controler_integrite
from .outils import ResultatTest
from .parametres import Parametres, charger_parametres
from .tests_declarations import TESTS_DECLARATIONS
from .tests_kyc import TESTS_KYC
from .tests_operations import TESTS_OPERATIONS

BLOC_COUVERTURE = "Efficacité du dispositif"
# Poids de priorisation (jugement de l'auditeur) : orientent la revue, ne qualifient pas un soupçon.
POIDS = {
    "OPE-01": 3,
    "OPE-02": 3,
    "OPE-03": 3,
    "OPE-04": 3,
    "OPE-05": 3,
    "OPE-06": 3,
    "DEC-01": 2,
    "KYC-01": 1,
    "KYC-02": 1,
    "KYC-03": 1,
    "KYC-04": 2,
    "KYC-05": 1,
    "KYC-06": 1,
    "COU-01": 2,
}


@dataclass
class ResultatsAudit:
    parametres: Parametres
    donnees: Donnees
    integrite: pd.DataFrame
    tests: dict[str, ResultatTest]
    priorisation: pd.DataFrame

    def __getitem__(self, code: str) -> ResultatTest:
        return self.tests[code]

    def synthese(self) -> pd.DataFrame:
        """Une ligne par test : population, exceptions, montant concerné."""
        return pd.DataFrame(
            [
                {
                    "code": t.code,
                    "bloc": t.bloc,
                    "test": t.titre,
                    "unite": t.unite,
                    "population": t.nb_population,
                    "exceptions": t.nb_exceptions,
                    "taux_exceptions": t.taux,
                    "clients_concernes": len(t.clients),
                    "montant_concerne": t.montant_exceptions,
                    "references": t.references,
                }
                for t in self.tests.values()
            ]
        )


def cou_01_couverture(d: Donnees, tests: dict[str, ResultatTest]) -> ResultatTest:
    """Clients identifiés par les scénarios de l'audit sans aucune alerte du dispositif de la banque."""
    alertes = set(d.alertes["id_client"].dropna())
    codes = [c for c in tests if c.startswith("OPE-")]
    lignes, par_test = {}, []
    for code in codes:
        clients = tests[code].clients
        par_test.append(
            {
                "test": code,
                "titre": tests[code].titre,
                "clients_identifies": len(clients),
                "clients_avec_alerte": len(clients & alertes),
                "taux_couverture": len(clients & alertes) / len(clients) if clients else None,
            }
        )
        for cid in clients:
            lignes.setdefault(cid, []).append(code)
    identifies = pd.DataFrame(
        [{"id_client": cid, "tests_declenches": ", ".join(sorted(t)), "nb_tests": len(t)} for cid, t in lignes.items()],
        columns=["id_client", "tests_declenches", "nb_tests"],
    )
    identifies["alerte_banque"] = identifies["id_client"].isin(alertes).map({True: "OUI", False: "NON"})
    decisions = d.alertes.groupby("id_client")["decision"].agg(set)

    def statut(cid: str) -> str:
        valeurs = decisions.get(cid, set())
        if not valeurs:
            return "Aucune alerte"
        if "DECLARATION_SOUPCON" in valeurs:
            return "Déclaration de soupçon transmise"
        if "EN_COURS" in valeurs:
            return "Alerte en cours d'analyse"
        return "Alerte(s) classée(s) sans suite"

    identifies["traitement_banque"] = identifies["id_client"].map(statut)
    ref = d.clients.set_index("id_client")
    identifies["agence"] = identifies["id_client"].map(ref["agence"])
    identifies["niveau_risque"] = identifies["id_client"].map(ref["niveau_risque"])
    non_couverts = (
        identifies[identifies["alerte_banque"] == "NON"]
        .sort_values(["nb_tests", "id_client"], ascending=[False, True])
        .reset_index(drop=True)
    )
    total = len(identifies)
    par_test.append(
        {
            "test": "Ensemble",
            "titre": "Clients identifiés par au moins un scénario de l'audit",
            "clients_identifies": total,
            "clients_avec_alerte": total - len(non_couverts),
            "taux_couverture": (total - len(non_couverts)) / total if total else None,
        }
    )
    return ResultatTest(
        code="COU-01",
        bloc=BLOC_COUVERTURE,
        titre="Couverture du dispositif de surveillance",
        objectif=(
            "Mesurer la part des clients à risque identifiés par l'audit (OPE-01 à OPE-06) qui n'ont fait "
            "l'objet d'aucune alerte de l'outil de la banque sur la période."
        ),
        references=(
            "Instruction BCEAO n°001-03-2025, art. 6 (SI de surveillance, révision annuelle) et art. 11 "
            "(évaluation au moins annuelle du dispositif)."
        ),
        parametres={"tests_pris_en_compte": ", ".join(codes)},
        unite="clients",
        nb_population=total,
        exceptions=non_couverts,
        annexes={
            "couverture_par_test": pd.DataFrame(par_test),
            "clients_identifies": identifies,
            "traitement_banque": identifies["traitement_banque"]
            .value_counts()
            .rename_axis("traitement")
            .reset_index(name="nb_clients"),
        },
        commentaire=f"{len(non_couverts)} client(s) sur {total} sans aucune alerte de la banque.",
    )


def prioriser(tests: dict[str, ResultatTest], d: Donnees) -> pd.DataFrame:
    """Score de priorisation des revues sur pièces (pondérations de l'auditeur)."""
    scores: dict[str, dict] = {}
    for code, t in tests.items():
        if code == "FIL-01":
            for _, r in t.exceptions.iterrows():
                poids = 5 if r["qualification"].startswith("Correspondance forte") else 1
                s = scores.setdefault(r["id_client"], {"score": 0, "tests": set()})
                s["score"] += poids
                s["tests"].add(code)
            continue
        for cid in t.clients:
            s = scores.setdefault(cid, {"score": 0, "tests": set()})
            if code not in s["tests"]:
                s["score"] += POIDS.get(code, 1)
                s["tests"].add(code)
    ref = d.clients.set_index("id_client")
    table = pd.DataFrame(
        [
            {"id_client": cid, "score": v["score"], "nb_tests": len(v["tests"]), "tests": ", ".join(sorted(v["tests"]))}
            for cid, v in scores.items()
        ],
        columns=["id_client", "score", "nb_tests", "tests"],
    )
    table["type_client"] = table["id_client"].map(ref["type_client"])
    table["agence"] = table["id_client"].map(ref["agence"])
    table["niveau_risque"] = table["id_client"].map(ref["niveau_risque"])
    return table.sort_values(["score", "nb_tests", "id_client"], ascending=[False, False, True]).reset_index(drop=True)


def executer_audit(donnees: Donnees | None = None, p: Parametres | None = None) -> ResultatsAudit:
    """Charge les données (si besoin), contrôle leur intégrité et exécute les 18 tests."""
    p = p or charger_parametres()
    d = donnees or charger_donnees(p.dossier_donnees)
    integrite = controler_integrite(d, p)
    tests: dict[str, ResultatTest] = {}
    for fonction in TESTS_OPERATIONS + TESTS_KYC + TESTS_DECLARATIONS:
        resultat = fonction(d, p)
        tests[resultat.code] = resultat
    tests["COU-01"] = cou_01_couverture(d, tests)
    ordre = [
        "OPE-01",
        "OPE-02",
        "OPE-03",
        "OPE-04",
        "OPE-05",
        "OPE-06",
        "COU-01",
        "FIL-01",
        "DEC-01",
        "ALE-01",
        "ALE-02",
        "ALE-03",
        "KYC-01",
        "KYC-02",
        "KYC-03",
        "KYC-04",
        "KYC-05",
        "KYC-06",
    ]
    tests = {code: tests[code] for code in ordre}
    return ResultatsAudit(parametres=p, donnees=d, integrite=integrite, tests=tests, priorisation=prioriser(tests, d))
