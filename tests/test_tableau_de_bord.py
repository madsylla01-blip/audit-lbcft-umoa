"""Test de fumée du tableau de bord (exécuté seulement si Streamlit est installé)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APPLICATION = Path(__file__).resolve().parents[1] / "app" / "tableau_de_bord.py"


def test_le_tableau_de_bord_se_charge_sans_erreur():
    at = AppTest.from_file(str(APPLICATION), default_timeout=300)
    at.run()
    assert not at.exception
    assert any("Audit du dispositif LBC/FT" in titre.value for titre in at.title)


def test_changement_de_test_et_de_client():
    at = AppTest.from_file(str(APPLICATION), default_timeout=300)
    at.run()
    for code in ("OPE-05", "OPE-06", "COU-01"):
        at.selectbox(key="test_ope").set_value(code).run()
        assert not at.exception, code
