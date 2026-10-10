"""Tableau de bord de l'audit LBC/FT (Streamlit).

Lancement, depuis la racine du projet :
    streamlit run app/tableau_de_bord.py

Toutes les données affichées sont fictives (Banque Fictive de l'Union).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from lbcft_audit import graphiques as g  # noqa: E402
from lbcft_audit.constats import opinion, points_forts, rediger_constats  # noqa: E402
from lbcft_audit.export_excel import exporter_excel  # noqa: E402
from lbcft_audit.generation import ecrire_jeu_de_donnees  # noqa: E402
from lbcft_audit.moteur import ResultatsAudit, executer_audit  # noqa: E402
from lbcft_audit.outils import fcfa, nom_pays, nombre, pourcentage  # noqa: E402
from lbcft_audit.parametres import charger_parametres  # noqa: E402
from lbcft_audit.pseudonymisation import masquer_nom  # noqa: E402

st.set_page_config(page_title="Audit LBC/FT — UMOA", layout="wide")

MOTS_MONTANTS = ("montant", "credit", "debit", "cumul", "revenu")


# ---------------------------------------------------------------------------- données
@st.cache_resource(show_spinner="Exécution des tests d'audit sur 100 % des données…")
def charger_resultats() -> ResultatsAudit:
    p = charger_parametres()
    if not (p.dossier_donnees / "operations.csv").exists():
        ecrire_jeu_de_donnees(p)
    return executer_audit(p=p)


@st.cache_resource(show_spinner="Préparation du classeur Excel…")
def classeur_excel(_r: ResultatsAudit) -> bytes:
    with tempfile.TemporaryDirectory() as dossier:
        chemin = exporter_excel(_r, Path(dossier) / "resultats_audit_lbcft.xlsx")
        return chemin.read_bytes()


def en_millions(table: pd.DataFrame) -> pd.DataFrame:
    """Montants affichés en millions de FCFA (une décimale), colonnes renommées en conséquence."""
    sortie = table.copy()
    for colonne in sortie.columns:
        if any(m in colonne for m in MOTS_MONTANTS) and pd.api.types.is_numeric_dtype(sortie[colonne]):
            sortie[colonne] = (sortie[colonne] / 1e6).round(1)
            sortie = sortie.rename(columns={colonne: f"{colonne} (M FCFA)"})
    return sortie


def afficher_table(table: pd.DataFrame, cle: str, masquer: bool) -> None:
    sortie = table.copy()
    if masquer:
        for colonne in ("nom_client", "nom_complet"):
            if colonne in sortie.columns:
                sortie[colonne] = sortie[colonne].map(masquer_nom)
    if "pays_contrepartie" in sortie.columns:
        sortie.insert(
            sortie.columns.get_loc("pays_contrepartie") + 1, "pays", sortie["pays_contrepartie"].map(nom_pays)
        )
    st.dataframe(en_millions(sortie), hide_index=True)
    st.download_button(
        "Télécharger (CSV)",
        sortie.to_csv(index=False, sep=";").encode("utf-8-sig"),
        file_name=f"{cle}.csv",
        mime="text/csv",
        key=f"csv_{cle}",
    )


def fiche_test(r: ResultatsAudit, code: str, masquer: bool) -> None:
    t = r[code]
    st.markdown(f"**Objectif.** {t.objectif}")
    st.caption(f"Références : {t.references}")
    c1, c2, c3 = st.columns(3)
    unite_population = "clients" if t.unite == "correspondances" else t.unite
    c1.metric("Population testée", f"{nombre(t.nb_population)} {unite_population}")
    c2.metric("Exceptions", f"{nombre(t.nb_exceptions)} {t.unite}")
    c3.metric("Montant concerné", fcfa(t.montant_exceptions, "M") if t.montant_exceptions else "—")
    with st.expander("Paramètres du test"):
        st.dataframe(
            pd.DataFrame({"paramètre": list(t.parametres), "valeur": [str(v) for v in t.parametres.values()]}),
            hide_index=True,
        )
    if t.commentaire:
        st.info(t.commentaire)
    if t.exceptions.empty:
        st.success("Aucune exception.")
    else:
        afficher_table(t.exceptions, code, masquer)


# ---------------------------------------------------------------------------- page
r = charger_resultats()
p, d = r.parametres, r.donnees
constats = rediger_constats(r)

with st.sidebar:
    st.title("Audit LBC/FT")
    st.caption(f"{p.banque} — **données 100 % fictives**")
    st.markdown(
        f"**Période testée** : {p.periode_debut:%d/%m/%Y} – {p.periode_fin:%d/%m/%Y}  \n"
        f"**Date d'arrêté** : {p.date_arrete:%d/%m/%Y}  \n"
        f"**Listes du GAFI** : {pd.Timestamp(p['listes_gafi']['date_reference']):%d/%m/%Y}"
    )
    masquer = st.checkbox(
        "Masquer les noms des clients", value=True, help="Bonne pratique sur données réelles (secret bancaire)."
    )
    st.download_button(
        "Feuilles de travail Excel",
        classeur_excel(r),
        file_name="resultats_audit_lbcft.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.divider()
    st.caption(
        "L'audit ne qualifie pas le soupçon : les exceptions sont vérifiées sur pièces puis "
        "transmises à la conformité, seule habilitée à déclarer à la CENTIF."
    )

st.title("Audit du dispositif LBC/FT d'une banque de l'UMOA")
st.caption("Réexécution exhaustive de 18 tests sur 12 mois d'activité — projet pédagogique, données fictives.")

onglets = st.tabs(
    [
        "Synthèse",
        "Surveillance des opérations",
        "Alertes et déclarations",
        "KYC et filtrage",
        "Fiche client",
        "Constats",
        "Méthode",
    ]
)

# ---------------------------------------------------------------- 1. Synthèse
with onglets[0]:
    couverture = r["COU-01"].annexes["couverture_par_test"].set_index("test").loc["Ensemble"]
    credits = d.operations.loc[d.operations["sens"] == "C", "montant"].sum()
    fil = r["FIL-01"].exceptions
    fortes = int(fil["qualification"].str.startswith("Correspondance forte").sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clients testés", nombre(len(d.clients)))
    c2.metric("Opérations testées", nombre(len(d.operations)), help=f"Crédits de la période : {fcfa(credits, 'Md')}")
    c3.metric(
        "Clients à risque sans alerte",
        f"{r['COU-01'].nb_exceptions} / {int(couverture.clients_identifies)}",
        help="Clients identifiés par les scénarios de l'audit (OPE-01 à OPE-06) sans aucune alerte de la banque",
    )
    c4.metric("Correspondances fortes (sanctions)", fortes)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Opinion proposée", opinion(constats))
    c6.metric("Constats", len(constats), help=", ".join(f"{c.numero} : {c.notation}" for c in constats))
    c7.metric("Alertes en souffrance", r["ALE-01"].nb_exceptions)
    c8.metric("DTE manquantes", r["DEC-01"].nb_exceptions)

    gauche, droite = st.columns(2)
    with gauche:
        st.pyplot(g.fig_couverture(r))
    with droite:
        st.pyplot(g.fig_clients_par_test(r))
    st.subheader("Résultats par test")
    synthese = r.synthese()
    synthese["taux_exceptions"] = (synthese["taux_exceptions"] * 100).round(1)
    st.dataframe(en_millions(synthese.rename(columns={"taux_exceptions": "taux_exceptions (%)"})), hide_index=True)
    st.subheader("Points forts relevés")
    for point in points_forts(r):
        st.markdown(f"- {point}")

# ---------------------------------------------------------------- 2. Opérations
with onglets[1]:
    codes = [c for c in r.tests if c.startswith("OPE-")] + ["COU-01"]
    code = st.selectbox("Test", codes, format_func=lambda c: f"{c} — {r[c].titre}", key="test_ope")
    fiche_test(r, code, masquer)
    t = r[code]
    if code == "OPE-01" and not t.exceptions.empty:
        client = st.selectbox("Client à visualiser", t.exceptions["id_client"].tolist(), key="client_ope01")
        st.pyplot(g.fig_fractionnement(r, client))
    elif code in ("OPE-02", "OPE-03", "OPE-04") and not t.exceptions.empty:
        client = st.selectbox("Client à visualiser", t.exceptions["id_client"].tolist(), key=f"client_{code}")
        st.pyplot(g.fig_flux_mensuels(r, client))
    elif code == "OPE-05":
        st.pyplot(g.fig_pays(r))
        st.markdown("**Écarts entre la liste de la banque et les listes du GAFI**")
        ecarts = t.annexes["ecarts_liste"].assign(nom=lambda x: x["pays"].map(nom_pays))
        st.dataframe(ecarts[["pays", "nom", "ecart"]], hide_index=True)
    elif code == "OPE-06" and not t.exceptions.empty:
        groupe = st.selectbox("Groupe", sorted(t.exceptions["groupe"].unique()), key="groupe_ope06")
        st.pyplot(g.fig_reseau(r, groupe))
    elif code == "COU-01":
        st.pyplot(g.fig_couverture(r))
        st.dataframe(r["COU-01"].annexes["traitement_banque"], hide_index=True)

# ---------------------------------------------------------------- 3. Alertes et déclarations
with onglets[2]:
    gauche, droite = st.columns(2)
    with gauche:
        st.pyplot(g.fig_alertes_age(r))
        st.dataframe(r["ALE-01"].annexes["par_analyste"], hide_index=True)
    with droite:
        st.pyplot(g.fig_delais_ds(r))
        st.pyplot(g.fig_taux_par_agence(r, "DEC-01"))
    code = st.selectbox(
        "Test", ["ALE-01", "ALE-02", "ALE-03", "DEC-01"], format_func=lambda c: f"{c} — {r[c].titre}", key="test_ale"
    )
    fiche_test(r, code, masquer)

# ---------------------------------------------------------------- 4. KYC et filtrage
with onglets[3]:
    st.subheader("Filtrage des listes de sanctions")
    st.warning("Liste de sanctions FICTIVE, créée pour la démonstration.")
    fiche_test(r, "FIL-01", masquer)
    st.divider()
    gauche, droite = st.columns([3, 2])
    with gauche:
        code = st.selectbox(
            "Test KYC",
            [c for c in r.tests if c.startswith("KYC-")],
            format_func=lambda c: f"{c} — {r[c].titre}",
            key="test_kyc",
        )
    with droite:
        st.pyplot(g.fig_taux_par_agence(r, "KYC-01"))
    fiche_test(r, code, masquer)

# ---------------------------------------------------------------- 5. Fiche client
with onglets[4]:
    st.caption(
        "Clients classés par score de priorisation : le score oriente l'ordre des revues sur pièces, "
        "il ne qualifie pas un soupçon."
    )
    prio = r.priorisation.set_index("id_client")
    client = st.selectbox(
        "Client",
        prio.index.tolist(),
        format_func=lambda c: f"{c} — score {int(prio.at[c, 'score'])} — {prio.at[c, 'tests']}",
        key="fiche_client",
    )
    fiche = d.clients.set_index("id_client").loc[client]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Type", "Personne physique" if fiche["type_client"] == "PP" else "Personne morale")
    c2.metric("Niveau de risque (banque)", fiche["niveau_risque"])
    c3.metric("Agence", fiche["agence"])
    c4.metric("PPE", fiche["ppe"] if pd.notna(fiche["ppe"]) else "—")
    profil = fiche["profession"] if fiche["type_client"] == "PP" else fiche["secteur_activite"]
    reference = (
        fiche["revenu_mensuel_declare"] if fiche["type_client"] == "PP" else fiche["chiffre_affaires_annuel_declare"]
    )
    revue = fiche["date_derniere_revue_kyc"]
    st.markdown(
        f"**Nom** : {masquer_nom(fiche['nom_complet']) if masquer else fiche['nom_complet']} · "
        f"**Profession / secteur** : {profil if pd.notna(profil) else 'non renseigné'} · "
        f"**{'Revenu mensuel' if fiche['type_client'] == 'PP' else 'CA annuel'} déclaré** : "
        f"{fcfa(reference) if pd.notna(reference) else 'non renseigné'} · "
        f"**Entrée en relation** : {fiche['date_entree_relation']:%d/%m/%Y} · "
        f"**Dernière revue KYC** : {f'{revue:%d/%m/%Y}' if pd.notna(revue) else '—'}"
    )
    declenches = [code for code, t in r.tests.items() if client in t.clients]
    st.markdown("**Tests déclenchés** : " + (", ".join(f"{c} ({r[c].titre})" for c in declenches) or "aucun"))
    st.pyplot(g.fig_flux_mensuels(r, client))
    alertes = d.alertes[d.alertes["id_client"] == client]
    st.markdown(f"**Alertes de la banque sur ce client** : {len(alertes)}")
    if len(alertes):
        st.dataframe(alertes, hide_index=True)
    operations = d.operations[d.operations["id_client"] == client].sort_values("date_operation", ascending=False)
    st.markdown(f"**Opérations de la période** : {nombre(len(operations))} (200 plus récentes affichées)")
    afficher_table(operations.head(200), f"operations_{client}", masquer)

# ---------------------------------------------------------------- 6. Constats
with onglets[5]:
    st.subheader(f"Opinion proposée : {opinion(constats)}")
    st.caption(
        "Projet à valider : faits calculés, causes présumées à confirmer en entretien, réponses des "
        "audités à recueillir."
    )
    for c in constats:
        with st.expander(f"{c.numero} — {c.titre} ({c.notation})", expanded=c.notation == "Critique"):
            st.markdown(f"**Critère.** {c.critere}")
            st.markdown(f"**Constat.** {c.constat}")
            st.markdown(f"**Cause.** {c.cause}")
            st.markdown(f"**Conséquence.** {c.consequence}")
            st.markdown(f"**Recommandation.** {c.recommandation}")
            st.caption(
                f"Tests : {', '.join(c.tests)} · Responsable proposé : {c.responsable} · "
                f"Échéance proposée : {c.echeance}"
            )
    st.subheader("Plan d'action proposé")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Constat": c.numero,
                    "Titre": c.titre,
                    "Notation": c.notation,
                    "Responsable": c.responsable,
                    "Échéance": c.echeance,
                }
                for c in constats
            ]
        ),
        hide_index=True,
    )

# ---------------------------------------------------------------- 7. Méthode
with onglets[6]:
    st.markdown(f"""
**Problématique.** Le dispositif de surveillance LBC/FT de la banque détecte-t-il réellement les opérations
à risque, et les alertes sont-elles traitées et déclarées à temps ? L'Instruction BCEAO n°001-03-2025
prévoit que ce dispositif soit audité au moins une fois par an.

**Démarche.**
1. Contrôles d'intégrité des extractions (clés, période, cohérence, totaux à rapprocher).
2. Réexécution indépendante de 18 tests sur 100 % des populations, paramétrés dans `config/parametres.yaml`.
3. Mesure de la couverture : les clients identifiés par l'audit ont-ils déclenché une alerte de la banque ?
4. Qualification des exceptions sur pièces, puis constats au format 5C et plan d'action.

**Garde-fous.** Données 100 % fictives ; noms masqués par défaut ; l'audit ne déclare pas à la CENTIF ;
chaque seuil réglementaire est sourcé, chaque hypothèse d'audit est signalée.

**Chiffres de la démonstration.** {nombre(len(d.clients))} clients, {nombre(len(d.operations))} opérations,
{nombre(len(d.alertes))} alertes ; {pourcentage(r["COU-01"].nb_exceptions, int(couverture.clients_identifies))}
des clients à risque identifiés n'ont déclenché aucune alerte.

Documentation complète : dossier `docs/` du dépôt (cadre réglementaire, méthodologie, matrice des risques,
programme de travail, catalogue des tests, rapport de mission, évaluation des tests).
""")
