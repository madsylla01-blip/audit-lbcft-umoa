"""Le générateur est reproductible et produit des données cohérentes."""

from __future__ import annotations

import pandas as pd
import pytest

from lbcft_audit.generation import generer_donnees


@pytest.fixture(scope="module")
def jeu(parametres):
    return generer_donnees(parametres)


def test_generation_reproductible(parametres, jeu):
    d1, v1, _ = jeu
    d2, v2, _ = generer_donnees(parametres)
    pd.testing.assert_frame_equal(d1.operations, d2.operations)
    pd.testing.assert_frame_equal(d1.clients, d2.clients)
    pd.testing.assert_frame_equal(v1, v2)


def test_coherence_des_tables(parametres, jeu):
    p = parametres
    d, verite, _ = jeu
    assert d.clients["id_client"].is_unique and d.operations["id_operation"].is_unique
    assert d.operations["id_compte"].isin(d.comptes["id_compte"]).all()
    assert (d.operations["montant"] > 0).all()
    assert d.operations["date_operation"].between(p.periode_debut, p.periode_fin + pd.Timedelta(days=1)).all()
    assert d.alertes["date_alerte"].max() <= p.date_arrete
    assert set(verite["id_client"]) <= set(d.clients["id_client"])
