"""Tests de bout en bout sur le jeu fictif livré : chaque anomalie injectée doit être détectée."""

from __future__ import annotations

from lbcft_audit.evaluation import charger_verite, evaluer


def test_integrite_sans_anomalie(resultats):
    assert (resultats.integrite["statut"] == "ANOMALIE").sum() == 0


def test_rappel_et_precision_des_scenarios(resultats, parametres):
    evaluation = evaluer(resultats, charger_verite(parametres.dossier_donnees)).set_index("test")
    assert (evaluation["rappel"] == 1.0).all(), evaluation
    assert (evaluation["precision"] >= 0.75).all(), evaluation


def test_kyc_correspond_aux_anomalies_injectees(resultats, meta):
    assert resultats["KYC-02"].clients == set(meta["pieces_expirees"])
    assert resultats["KYC-05"].clients == set(meta["pm_sans_be"])
    assert set(meta["kyc_incomplets"]) <= resultats["KYC-01"].clients
    assert set(meta["revues_en_retard"]) <= resultats["KYC-03"].clients
    attendues = set(meta["ppe_sans_approbation"]) | set(meta["ppe_mal_classees"]) | set(meta["ppe_revue_depassee"])
    assert resultats["KYC-04"].clients == attendues


def test_alertes_et_declarations(resultats, meta):
    assert set(resultats["ALE-01"].exceptions["id_alerte"]) == set(meta["alertes_arriere"])
    assert set(meta["alertes_clotures_massives"]) <= set(resultats["ALE-02"].exceptions["id_alerte"])
    manquantes = {
        f"{r.id_client}|{r.date_operation:%Y-%m-%d}|{r.type_operation}"
        for r in resultats["DEC-01"].exceptions.itertuples()
    }
    assert manquantes == set(meta["dte_manquantes"])


def test_couverture_mesuree(resultats):
    couverture = resultats["COU-01"].annexes["couverture_par_test"].set_index("test")
    assert couverture.loc["OPE-06", "clients_avec_alerte"] == 0  # aucun réseau détecté par la banque
    assert 0 < resultats["COU-01"].nb_exceptions < couverture.loc["Ensemble", "clients_identifies"]
