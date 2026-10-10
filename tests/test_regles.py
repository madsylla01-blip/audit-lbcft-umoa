"""Tests unitaires des règles d'audit sur de petits jeux construits à la main."""

from __future__ import annotations

from conftest import client, donnees, table

from lbcft_audit.outils import normaliser_nom
from lbcft_audit.tests_declarations import ale_02_clotures_non_justifiees, dec_01_declarations_especes
from lbcft_audit.tests_kyc import fil_01_filtrage_sanctions, kyc_03_revues_en_retard, kyc_04_ppe
from lbcft_audit.tests_operations import (
    ope_01_fractionnement,
    ope_02_comptes_de_passage,
    ope_04_reactivation,
    ope_06_reseaux,
)


def op(numero: int, id_client: str, date: str, type_operation: str, montant: float, agence: str = "AG01") -> dict:
    sens = "C" if type_operation in ("VERSEMENT_ESPECES", "VIREMENT_RECU", "TRANSFERT_INT_RECU") else "D"
    return {
        "id_operation": f"OP{numero:05d}",
        "date_operation": date,
        "id_compte": f"CP{id_client}",
        "id_client": id_client,
        "type_operation": type_operation,
        "sens": sens,
        "montant": montant,
        "canal": "GUICHET",
        "agence_operation": agence,
    }


def comptes_pour(*clients: str, dernier_mouvement: str = "2025-06-15") -> list[dict]:
    return [
        {
            "id_compte": f"CP{c}",
            "id_client": c,
            "type_compte": "COURANT",
            "agence": "AG01",
            "date_ouverture": "2015-01-01",
            "date_dernier_mouvement_avant_periode": dernier_mouvement,
        }
        for c in clients
    ]


def test_normalisation_des_noms():
    assert normaliser_nom("Seydou KANTÉ") == normaliser_nom("KANTE Seydou") == "KANTE SEYDOU"
    assert normaliser_nom("KORALIS NÉGOCE SARL") == "KORALIS NEGOCE"
    assert normaliser_nom(None) == ""


def test_fractionnement(parametres):
    ops = [
        # C1 : 3 versements dans la bande (70 % - 100 % du seuil) en 5 jours => fractionnement
        op(1, "C1", "2025-09-01 10:00", "VERSEMENT_ESPECES", 12_000_000, "AG01"),
        op(2, "C1", "2025-09-03 10:00", "VERSEMENT_ESPECES", 11_000_000, "AG02"),
        op(3, "C1", "2025-09-05 10:00", "VERSEMENT_ESPECES", 13_000_000, "AG03"),
        # C2 : seulement 2 versements
        op(4, "C2", "2025-09-01 10:00", "VERSEMENT_ESPECES", 12_000_000),
        op(5, "C2", "2025-09-02 10:00", "VERSEMENT_ESPECES", 12_000_000),
        # C3 : 3 versements étalés sur 10 jours
        op(6, "C3", "2025-09-01 10:00", "VERSEMENT_ESPECES", 12_000_000),
        op(7, "C3", "2025-09-06 10:00", "VERSEMENT_ESPECES", 12_000_000),
        op(8, "C3", "2025-09-11 10:00", "VERSEMENT_ESPECES", 12_000_000),
        # C4 : 3 petits versements hors de la bande
        op(9, "C4", "2025-09-01 10:00", "VERSEMENT_ESPECES", 4_000_000),
        op(10, "C4", "2025-09-02 10:00", "VERSEMENT_ESPECES", 4_000_000),
        op(11, "C4", "2025-09-03 10:00", "VERSEMENT_ESPECES", 4_000_000),
    ]
    d = donnees(
        clients=table("clients", [client(c) for c in ("C1", "C2", "C3", "C4")]),
        comptes=table("comptes", comptes_pour("C1", "C2", "C3", "C4")),
        operations=table("operations", ops),
    )
    resultat = ope_01_fractionnement(d, parametres)
    assert resultat.clients == {"C1"}
    ligne = resultat.exceptions.iloc[0]
    assert ligne["nb_versements"] == 3 and ligne["montant_total"] == 36_000_000 and ligne["nb_agences"] == 3


def test_compte_de_passage(parametres):
    ops, n = [], 0
    for mois in ("2025-08", "2025-10", "2025-12"):
        for cid, sortie in (("P1", 11_800_000), ("P2", 5_000_000)):
            n += 2
            ops.append(op(n, cid, f"{mois}-10 09:00", "VIREMENT_RECU", 12_000_000))
            ops.append(op(n + 1, cid, f"{mois}-11 15:00", "RETRAIT_ESPECES", sortie))
    d = donnees(
        clients=table("clients", [client("P1"), client("P2")]),
        comptes=table("comptes", comptes_pour("P1", "P2")),
        operations=table("operations", ops),
    )
    resultat = ope_02_comptes_de_passage(d, parametres)
    assert resultat.clients == {"P1"}
    assert resultat.exceptions.iloc[0]["nb_episodes"] == 3


def test_reactivation_compte_inactif(parametres):
    comptes = comptes_pour("R1", dernier_mouvement="2023-01-15") + comptes_pour("R2")
    ops = [
        op(1, "R1", "2025-09-01 10:00", "VIREMENT_RECU", 10_000_000),
        op(2, "R1", "2025-09-04 10:00", "RETRAIT_ESPECES", 9_000_000),
        op(3, "R2", "2025-09-01 10:00", "VIREMENT_RECU", 10_000_000),
    ]
    d = donnees(
        clients=table("clients", [client("R1"), client("R2")]),
        comptes=table("comptes", comptes),
        operations=table("operations", ops),
    )
    resultat = ope_04_reactivation(d, parametres)
    assert resultat.clients == {"R1"}
    assert resultat.exceptions.iloc[0]["jours_inactivite"] > 900


def test_reseau_identifiants_partages(parametres):
    clients = [
        client("N1", telephone="70 11 22 33"),
        client("N2", telephone="70112233"),
        client("N3", telephone="+226 70 11 22 33"),
        client("F1", adresse="Lot 9, Cité"),
        client("F2", adresse="lot 9 cite"),
    ]
    d = donnees(clients=table("clients", clients))
    resultat = ope_06_reseaux(d, parametres)
    assert resultat.clients == {"N1", "N2", "N3"}  # le foyer de 2 personnes n'atteint pas le seuil de 3


def test_declarations_especes_manquantes(parametres):
    ops = [
        op(1, "D1", "2025-10-01 09:00", "VERSEMENT_ESPECES", 9_000_000),
        op(2, "D1", "2025-10-01 15:00", "VERSEMENT_ESPECES", 7_000_000),  # 16 M liés le même jour
        op(3, "D2", "2025-10-02 09:00", "RETRAIT_ESPECES", 20_000_000),
        op(4, "D3", "2025-10-03 09:00", "VERSEMENT_ESPECES", 14_000_000),
    ]  # sous le seuil
    registre = table(
        "declarations_especes",
        [
            {
                "id_dte": "DTE1",
                "id_client": "D2",
                "date_operation": "2025-10-02",
                "type_operation": "RETRAIT_ESPECES",
                "montant_declare": 20_000_000,
                "date_declaration": "2025-10-05",
            }
        ],
    )
    d = donnees(
        clients=table("clients", [client(c) for c in ("D1", "D2", "D3")]),
        operations=table("operations", ops),
        declarations_especes=registre,
    )
    resultat = dec_01_declarations_especes(d, parametres)
    assert resultat.nb_population == 2
    assert resultat.clients == {"D1"}


def test_filtrage_approche(parametres):
    clients = [
        client("S1", nom_complet="Seydou KANTÉ", date_naissance="1979-11-04"),
        client("S2", nom_complet="Aminata SANGARÉ", date_naissance="1994-05-12"),
        client("S3", nom_complet="Moussa DIARRA"),
    ]
    liste = table(
        "liste_sanctions",
        [
            {"id_entree": "L1", "nom": "KANTE Seydou", "type_entite": "PP", "date_naissance": "1979-11-04"},
            {"id_entree": "L2", "nom": "SANGARE Aminata", "type_entite": "PP", "date_naissance": "1968-09-30"},
        ],
    )
    resultat = fil_01_filtrage_sanctions(donnees(clients=table("clients", clients), liste_sanctions=liste), parametres)
    qualif = resultat.exceptions.set_index("id_client")["qualification"]
    assert set(qualif.index) == {"S1", "S2"}
    assert qualif["S1"].startswith("Correspondance forte")
    assert qualif["S2"].startswith("Homonymie")


def test_ppe_et_revues(parametres):
    clients = [
        client("K1", ppe="OUI", ppe_approbation_direction="NON", niveau_risque="FAIBLE"),
        client(
            "K2",
            ppe="OUI",
            ppe_approbation_direction="OUI",
            niveau_risque="ELEVE",
            date_derniere_revue_kyc="2026-01-15",
        ),
        client("K3", niveau_risque="ELEVE", date_derniere_revue_kyc="2025-01-01"),
        client("K4", niveau_risque="FAIBLE", date_derniere_revue_kyc="2024-01-01"),
    ]
    d = donnees(clients=table("clients", clients))
    ppe = kyc_04_ppe(d, parametres)
    assert ppe.clients == {"K1"}
    assert "approbation_direction_absente" in ppe.exceptions.iloc[0]["anomalies"]
    assert kyc_03_revues_en_retard(d, parametres).clients == {"K3"}


def test_clotures_en_masse_et_sans_motif(parametres):
    alertes = [
        {
            "id_alerte": f"A{i:03d}",
            "id_client": f"X{i}",
            "scenario": "ESP-01",
            "date_alerte": "2025-12-01",
            "analyste": "A04",
            "statut": "CLOTUREE",
            "date_cloture": "2025-12-31",
            "motif_cloture": "Clôture groupée",
            "decision": "CLASSEMENT_SANS_SUITE",
        }
        for i in range(16)
    ]
    alertes.append(
        {
            "id_alerte": "B001",
            "id_client": "Y1",
            "scenario": "PAY-01",
            "date_alerte": "2025-11-02",
            "analyste": "A01",
            "statut": "CLOTUREE",
            "date_cloture": "2025-11-05",
            "motif_cloture": None,
            "decision": "CLASSEMENT_SANS_SUITE",
        }
    )
    resultat = ale_02_clotures_non_justifiees(donnees(alertes=table("alertes", alertes)), parametres)
    anomalies = resultat.exceptions.set_index("id_alerte")["anomalie"]
    assert len(anomalies) == 17
    assert anomalies["B001"] == "Clôture sans motif"
    assert anomalies["A000"].startswith("Clôture en masse")
