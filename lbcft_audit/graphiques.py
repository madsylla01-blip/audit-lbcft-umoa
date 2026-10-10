"""Graphiques (matplotlib) partagés par le tableau de bord, le README et le rapport.

Conventions : marques fines, grille discrète, une seule couleur d'accent pour le message
principal (le reste en gris), légende dès deux séries, chaque graphique ayant son tableau.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.dates import DateFormatter  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator  # noqa: E402

from .moteur import ResultatsAudit  # noqa: E402

SURFACE = "#fcfcfb"
ENCRE = "#0b0b0b"
ENCRE_2 = "#52514e"
ENCRE_ATTENUEE = "#898781"
GRILLE = "#e1e0d9"
AXE = "#c3c2b7"
GRIS_SERIE = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ACCENT = SERIES[0]
CRITIQUE = "#d03b3b"


def _figure(largeur: float = 8.0, hauteur: float = 4.2) -> tuple[Figure, object]:
    fig = Figure(figsize=(largeur, hauteur), dpi=110, facecolor=SURFACE)
    ax = fig.subplots()
    ax.set_facecolor(SURFACE)
    return fig, ax


def _style(ax, titre: str, sous_titre: str = "", axe_valeurs: str = "x") -> None:
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(AXE)
        ax.spines[cote].set_linewidth(1)
    ax.tick_params(colors=ENCRE_ATTENUEE, labelsize=9, length=0, pad=6)
    ax.grid(axis=axe_valeurs, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    fig = ax.get_figure()
    fig.text(0.01, 0.97, titre, ha="left", va="top", fontsize=12.5, fontweight="bold", color=ENCRE)
    if sous_titre:
        fig.text(0.01, 0.905, sous_titre, ha="left", va="top", fontsize=9.5, color=ENCRE_2)


def _millions(x, _pos=None) -> str:
    if abs(x) >= 1e9:
        return f"{x / 1e9:.1f} Md".replace(".", ",")
    if abs(x) >= 1e6:
        return f"{x / 1e6:.0f} M"
    if abs(x) >= 1e3:
        return f"{x / 1e3:.0f} k"
    return f"{x:.0f}"


def _pct(x: float, decimales: int = 0) -> str:
    return f"{100 * x:.{decimales}f} %".replace(".", ",")


def _entier(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


def _ajuster(fig: Figure, haut: float = 0.84, bas: float = 0.12, gauche: float = 0.08, droite: float = 0.97) -> None:
    fig.subplots_adjust(top=haut, bottom=bas, left=gauche, right=droite)


# ---------------------------------------------------------------------------
def fig_clients_par_test(r: ResultatsAudit) -> Figure:
    """Nombre de clients concernés par chaque test."""
    s = r.synthese()
    s = s[s["clients_concernes"] > 0].iloc[::-1]
    fig, ax = _figure(8.0, 5.2)
    etiquettes = [f"{c}  {t[:44]}{'…' if len(t) > 44 else ''}" for c, t in zip(s["code"], s["test"])]
    barres = ax.barh(etiquettes, s["clients_concernes"], height=0.6, color=ACCENT)
    for b, v in zip(barres, s["clients_concernes"]):
        ax.text(b.get_width() + 0.6, b.get_y() + b.get_height() / 2, f"{v}", va="center", fontsize=8.5, color=ENCRE_2)
    ax.tick_params(axis="y", labelsize=8.5, colors=ENCRE_2)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    _style(
        ax, "Clients concernés par test", "Exceptions à qualifier sur pièces — 1 client peut relever de plusieurs tests"
    )
    _ajuster(fig, haut=0.86, bas=0.07, gauche=0.47)
    return fig


def fig_couverture(r: ResultatsAudit) -> Figure:
    """Clients identifiés par l'audit : alertés ou non par l'outil de la banque."""
    c = r["COU-01"].annexes["couverture_par_test"]
    c = c[c["test"] != "Ensemble"].iloc[::-1].copy()
    c["non_alertes"] = c["clients_identifies"] - c["clients_avec_alerte"]
    fig, ax = _figure(8.0, 4.4)
    etiquettes = [f"{t}  {x[:38]}{'…' if len(x) > 38 else ''}" for t, x in zip(c["test"], c["titre"])]
    b1 = ax.barh(
        etiquettes,
        c["non_alertes"],
        height=0.6,
        color=ACCENT,
        edgecolor=SURFACE,
        linewidth=2,
        label="Sans aucune alerte de la banque",
    )
    ax.barh(
        etiquettes,
        c["clients_avec_alerte"],
        left=c["non_alertes"],
        height=0.6,
        color=GRIS_SERIE,
        edgecolor=SURFACE,
        linewidth=2,
        label="Avec au moins une alerte",
    )
    for barre, nb in zip(b1, c["non_alertes"]):
        if nb > 0:
            ax.text(
                barre.get_width() / 2,
                barre.get_y() + barre.get_height() / 2,
                f"{nb}",
                ha="center",
                va="center",
                fontsize=8.5,
                color="white",
                fontweight="bold",
            )
    total = r["COU-01"].annexes["couverture_par_test"].iloc[-1]
    part = 1 - total["clients_avec_alerte"] / total["clients_identifies"]
    ax.tick_params(axis="y", labelsize=8.5, colors=ENCRE_2)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc="lower right", frameon=False, fontsize=8.5, labelcolor=ENCRE_2)
    _style(
        ax,
        "Ce que le dispositif de la banque ne voit pas",
        f"{_pct(part)} des clients identifiés par l'audit n'ont déclenché aucune alerte sur 12 mois",
    )
    _ajuster(fig, haut=0.84, bas=0.08, gauche=0.45)
    return fig


def fig_fractionnement(r: ResultatsAudit, id_client: str | None = None) -> Figure:
    """Versements d'espèces d'un client : fractionnement sous le seuil de déclaration."""
    t = r["OPE-01"]
    if id_client is None:
        id_client = t.exceptions.sort_values("nb_versements", ascending=False)["id_client"].iloc[0]
    seuil = float(r.parametres.seuils["declaration_especes_centif"])
    ops = r.donnees.operations
    esp = ops[(ops["id_client"] == id_client) & (ops["type_operation"] == "VERSEMENT_ESPECES")]
    signales = esp["id_operation"].isin(t.detail["id_operation"]) if t.detail is not None else False
    fig, ax = _figure(8.0, 4.2)
    ax.axhspan(r.parametres.hypotheses["fractionnement"]["bande_basse"] * seuil, seuil, color=ACCENT, alpha=0.07, lw=0)
    ax.axhline(seuil, color=CRITIQUE, linewidth=1.4, linestyle=(0, (4, 3)))
    ax.text(
        esp["date_operation"].min(),
        seuil * 1.03,
        "Seuil de déclaration à la CENTIF : 15 M FCFA",
        fontsize=8.5,
        color=CRITIQUE,
        va="bottom",
    )
    autres = esp[~signales]
    ax.scatter(
        autres["date_operation"],
        autres["montant"],
        s=22,
        color=GRIS_SERIE,
        edgecolor=SURFACE,
        linewidth=1,
        label="Autres versements",
        zorder=3,
    )
    sel = esp[signales]
    ax.scatter(
        sel["date_operation"],
        sel["montant"],
        s=46,
        color=ACCENT,
        edgecolor=SURFACE,
        linewidth=2,
        label="Versements fractionnés (fenêtre de 7 jours)",
        zorder=4,
    )
    ax.yaxis.set_major_formatter(FuncFormatter(_millions))
    ax.yaxis.set_major_locator(MultipleLocator(5e6))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%y"))
    ax.set_ylim(0, seuil * 1.25)
    ax.legend(loc="center right", frameon=False, fontsize=8.5, labelcolor=ENCRE_2)
    total = sel["montant"].sum()
    _style(
        ax,
        f"Fractionnement : versements d'espèces du client {id_client}",
        f"{len(sel)} versements juste sous le seuil, {_entier(total / 1e6)} M FCFA au total, "
        f"dans {sel['agence_operation'].nunique()} agences",
        axe_valeurs="y",
    )
    _ajuster(fig, haut=0.84, bas=0.1, gauche=0.08)
    return fig


def fig_flux_mensuels(r: ResultatsAudit, id_client: str) -> Figure:
    """Crédits et débits mensuels d'un client, comparés au revenu (ou CA mensuel) déclaré."""
    ops = r.donnees.operations
    o = ops[ops["id_client"] == id_client]
    mois = pd.period_range(r.parametres.periode_debut, r.parametres.periode_fin, freq="M")
    flux = (
        o.assign(mois=o["date_operation"].dt.to_period("M"))
        .pivot_table(index="mois", columns="sens", values="montant", aggfunc="sum")
        .reindex(mois)
        .fillna(0)
    )
    for s in ("C", "D"):
        if s not in flux.columns:
            flux[s] = 0
    client = r.donnees.clients.set_index("id_client").loc[id_client]
    reference = client["revenu_mensuel_declare"]
    libelle_ref = "Revenu mensuel déclaré"
    if client["type_client"] == "PM":
        reference, libelle_ref = client["chiffre_affaires_annuel_declare"] / 12, "CA mensuel déclaré"
    x = np.arange(len(mois))
    fig, ax = _figure(8.0, 3.8)
    ax.plot(
        x,
        flux["C"],
        color=SERIES[0],
        linewidth=2,
        marker="o",
        markersize=5,
        markeredgecolor=SURFACE,
        markeredgewidth=1.5,
        label="Crédits",
    )
    ax.plot(
        x,
        flux["D"],
        color=SERIES[1],
        linewidth=2,
        marker="o",
        markersize=5,
        markeredgecolor=SURFACE,
        markeredgewidth=1.5,
        label="Débits",
    )
    if pd.notna(reference):
        ax.axhline(reference, color=ENCRE_ATTENUEE, linewidth=1.2, linestyle=(0, (4, 3)), label=libelle_ref)
    ax.set_xticks(x, [m.strftime("%m/%y") for m in mois])
    ax.yaxis.set_major_formatter(FuncFormatter(_millions))
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=8.5, ncol=3, labelcolor=ENCRE_2)
    _style(ax, f"Flux mensuels du client {id_client}", "Montants en FCFA", axe_valeurs="y")
    _ajuster(fig, haut=0.8, bas=0.1)
    return fig


def fig_reseau(r: ResultatsAudit, groupe: str | None = None) -> Figure:
    """Graphe d'un groupe de clients partageant un identifiant et, le cas échéant, un bénéficiaire."""
    ex = r["OPE-06"].exceptions
    if groupe is None:
        avec_benef = ex[ex["beneficiaire_commun"] != ""]
        base = avec_benef if len(avec_benef) else ex
        groupe = base.sort_values(["taille_groupe", "groupe"], ascending=[False, True])["groupe"].iloc[0]
    g_ex = ex[ex["groupe"] == groupe]
    identifiant = g_ex["identifiant_partage"].iloc[0]
    beneficiaire = g_ex["beneficiaire_commun"].iloc[0]
    graphe = nx.Graph()
    noeud_id = {"téléphone": "Téléphone partagé", "adresse": "Adresse partagée"}.get(identifiant, identifiant)
    graphe.add_node(noeud_id, role="identifiant")
    for _, m in g_ex.iterrows():
        graphe.add_node(m["id_client"], role="client")
        graphe.add_edge(m["id_client"], noeud_id)
        if beneficiaire:
            graphe.add_node(beneficiaire, role="beneficiaire")
            if m["montant_vers_beneficiaire"] > 0:
                graphe.add_edge(m["id_client"], beneficiaire, poids=m["montant_vers_beneficiaire"])
    # Disposition lisible : identifiant à gauche, clients au centre, bénéficiaire à droite
    clients_noeuds = [n for n, a in graphe.nodes(data=True) if a["role"] == "client"]
    pos = {n: (0.0, y) for n, y in zip(clients_noeuds, np.linspace(1, -1, len(clients_noeuds)))}
    pos[noeud_id] = (-1.2, 0.0)
    if beneficiaire:
        pos[beneficiaire] = (1.2, 0.0)
    fig, ax = _figure(8.0, 4.6)
    ax.axis("off")
    nx.draw_networkx_edges(graphe, pos, ax=ax, edge_color=AXE, width=1.4)
    couleurs = {"client": SERIES[0], "identifiant": SERIES[2], "beneficiaire": SERIES[1]}
    formes = {"client": "o", "identifiant": "s", "beneficiaire": "D"}
    for role in couleurs:
        noeuds = [n for n, a in graphe.nodes(data=True) if a["role"] == role]
        if noeuds:
            nx.draw_networkx_nodes(
                graphe,
                pos,
                nodelist=noeuds,
                ax=ax,
                node_color=couleurs[role],
                node_shape=formes[role],
                node_size=520 if role == "client" else 760,
                edgecolors=SURFACE,
                linewidths=2,
            )
    for noeud, (x, y) in pos.items():
        etiquette = noeud if len(noeud) <= 18 else noeud.replace(" ", "\n", 1)
        if graphe.nodes[noeud]["role"] == "client":
            ax.text(x + 0.09, y, etiquette, ha="left", va="center", fontsize=8.5, color=ENCRE)
        else:
            ax.text(x, y - 0.16, etiquette, ha="center", va="top", fontsize=8.5, color=ENCRE)
    ax.margins(x=0.12, y=0.12)
    legende = [
        Line2D([0], [0], marker=formes[k], color="w", markerfacecolor=v, markersize=10, label=lab)
        for k, v, lab in (
            ("client", SERIES[0], "Client"),
            ("identifiant", SERIES[2], "Identifiant partagé"),
            ("beneficiaire", SERIES[1], "Bénéficiaire commun des fonds"),
        )
        if any(a["role"] == k for _, a in graphe.nodes(data=True))
    ]
    ax.legend(handles=legende, loc="lower left", frameon=False, fontsize=8.5, labelcolor=ENCRE_2)
    montant = g_ex["montant_vers_beneficiaire"].sum()
    sous_titre = f"{len(g_ex)} clients, même {identifiant}"
    if beneficiaire:
        sous_titre += f" ; {_entier(montant / 1e6)} M FCFA envoyés au même bénéficiaire"
    _style(ax, f"Réseau {groupe} : clients liés par un identifiant partagé", sous_titre)
    ax.grid(False)
    _ajuster(fig, haut=0.86, bas=0.02, gauche=0.02, droite=0.98)
    return fig


def fig_pays(r: ResultatsAudit) -> Figure:
    """Transferts avec les pays listés par le GAFI : alertés ou non par la banque."""
    t = r["OPE-05"]
    exposes = (
        r.donnees.operations[r.donnees.operations["id_operation"].isin(set(t.exceptions["id_operation"]))]
        .groupby("pays_contrepartie")["montant"]
        .sum()
    )
    tous = t.annexes["par_pays"].groupby("pays_contrepartie")["montant"].sum()
    table = pd.DataFrame({"total": tous, "non_alerte": exposes}).fillna(0).sort_values("total")
    table["alerte"] = table["total"] - table["non_alerte"]
    fig, ax = _figure(8.0, 3.8)
    ax.barh(
        table.index,
        table["non_alerte"],
        height=0.6,
        color=ACCENT,
        edgecolor=SURFACE,
        linewidth=2,
        label="Sans alerte de la banque",
    )
    ax.barh(
        table.index,
        table["alerte"],
        left=table["non_alerte"],
        height=0.6,
        color=GRIS_SERIE,
        edgecolor=SURFACE,
        linewidth=2,
        label="Alertés",
    )
    ax.xaxis.set_major_formatter(FuncFormatter(_millions))
    ax.tick_params(axis="y", labelsize=9, colors=ENCRE_2)
    ax.legend(loc="lower right", frameon=False, fontsize=8.5, labelcolor=ENCRE_2)
    maj = pd.Timestamp(r.parametres["parametrage_banque"]["date_mise_a_jour_liste"])
    _style(
        ax,
        "Transferts avec des pays listés par le GAFI",
        f"Montants par pays (FCFA) — liste interne de la banque mise à jour le {maj:%d/%m/%Y}",
    )
    _ajuster(fig, haut=0.82, bas=0.1, gauche=0.08)
    return fig


def fig_alertes_age(r: ResultatsAudit) -> Figure:
    """Ancienneté des alertes ouvertes à la date d'arrêté."""
    a = r.donnees.alertes
    delai = int(r.parametres.hypotheses["alertes"]["delai_max_traitement_jours"])
    ouvertes = a[a["statut"] == "OUVERTE"]
    age = (r.parametres.date_arrete - ouvertes["date_alerte"]).dt.days
    tranches = pd.cut(
        age,
        bins=[-1, delai, 60, 90, 180, 10_000],
        labels=[f"0-{delai} j", f"{delai + 1}-60 j", "61-90 j", "91-180 j", "> 180 j"],
    )
    nb = tranches.value_counts().reindex(tranches.cat.categories, fill_value=0)
    fig, ax = _figure(8.0, 3.6)
    couleurs = [GRIS_SERIE] + [ACCENT] * (len(nb) - 1)
    barres = ax.bar(nb.index.astype(str), nb.values, width=0.55, color=couleurs)
    for b, v in zip(barres, nb.values):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3, f"{v}", ha="center", fontsize=9, color=ENCRE_2)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    hors = int(nb.iloc[1:].sum())
    _style(
        ax,
        "Alertes ouvertes par ancienneté",
        f"{hors} alerte(s) au-delà du délai de traitement de {delai} jours (procédure interne)",
        axe_valeurs="y",
    )
    _ajuster(fig, haut=0.8, bas=0.1)
    return fig


def fig_taux_par_agence(r: ResultatsAudit, code: str = "KYC-01") -> Figure:
    """Taux d'anomalies par agence (KYC-01 : dossiers incomplets ; DEC-01 : DTE manquantes)."""
    if code == "KYC-01":
        t = r["KYC-01"].annexes["par_agence"].set_index("agence")["taux_incomplets"]
        titre, sous = (
            "Dossiers KYC incomplets par agence",
            "Part des clients de l'agence avec au moins un champ obligatoire vide",
        )
    else:
        t = r["DEC-01"].annexes["par_agence"].set_index("agence")["taux_manquantes"]
        titre, sous = "DTE manquantes par agence", "Part des déclarations attendues absentes du registre"
    t = t.sort_values()
    fig, ax = _figure(8.0, 3.4)
    couleurs = [ACCENT if v == t.max() else GRIS_SERIE for v in t.values]
    barres = ax.barh(t.index, t.values, height=0.55, color=couleurs)
    for b, v in zip(barres, t.values):
        ax.text(
            b.get_width() + 0.003, b.get_y() + b.get_height() / 2, _pct(v), va="center", fontsize=8.5, color=ENCRE_2
        )
    ax.xaxis.set_major_locator(MultipleLocator(0.05 if t.max() <= 0.3 else 0.1))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _p: _pct(x)))
    ax.tick_params(axis="y", colors=ENCRE_2)
    _style(ax, titre, sous)
    _ajuster(fig, haut=0.8, bas=0.1, gauche=0.1)
    return fig


def fig_delais_ds(r: ResultatsAudit) -> Figure:
    """Délais d'analyse et de transmission des déclarations de soupçon (deux échelles => deux graphiques)."""
    h = r.parametres.hypotheses["declarations_soupcon"]
    ds = r["ALE-03"].annexes["distribution_delais"]
    fig = Figure(figsize=(8.0, 3.6), dpi=110, facecolor=SURFACE)
    axes = fig.subplots(1, 2)
    for ax, col, limite, lib in (
        (axes[0], "delai_analyse_jours", h["delai_max_analyse_jours"], "Analyse (alerte → décision)"),
        (axes[1], "delai_transmission_jours", h["delai_max_transmission_jours"], "Transmission (décision → CENTIF)"),
    ):
        ax.set_facecolor(SURFACE)
        valeurs = ds[col].sort_values().to_numpy()
        couleurs = [ACCENT if v > limite else GRIS_SERIE for v in valeurs]
        ax.bar(np.arange(len(valeurs)), valeurs, color=couleurs, width=0.7)
        ax.axhline(limite, color=CRITIQUE, linewidth=1.2, linestyle=(0, (4, 3)))
        ax.text(0, limite, f" délai cible : {limite} j", fontsize=8, color=CRITIQUE, va="bottom")
        ax.set_xticks([])
        for cote in ("top", "right"):
            ax.spines[cote].set_visible(False)
        for cote in ("left", "bottom"):
            ax.spines[cote].set_color(AXE)
        ax.tick_params(colors=ENCRE_ATTENUEE, labelsize=8.5, length=0)
        ax.grid(axis="y", color=GRILLE, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_title(lib, fontsize=9.5, color=ENCRE_2, loc="left")
    fig.text(
        0.01,
        0.97,
        "Délais des déclarations de soupçon (en jours, une barre par DS)",
        ha="left",
        va="top",
        fontsize=12.5,
        fontweight="bold",
        color=ENCRE,
    )
    fig.subplots_adjust(top=0.78, bottom=0.06, left=0.07, right=0.98, wspace=0.25)
    return fig


FIGURES_DOCS = {
    "clients_par_test.png": fig_clients_par_test,
    "couverture_dispositif.png": fig_couverture,
    "fractionnement_exemple.png": fig_fractionnement,
    "reseau_exemple.png": fig_reseau,
    "pays_gafi.png": fig_pays,
    "alertes_anciennete.png": fig_alertes_age,
    "kyc_par_agence.png": fig_taux_par_agence,
    "delais_ds.png": fig_delais_ds,
}


def exporter_figures(r: ResultatsAudit, dossier: str | Path, dpi: int = 160) -> list[Path]:
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    chemins = []
    for nom, fonction in FIGURES_DOCS.items():
        fig = fonction(r)
        chemin = dossier / nom
        fig.savefig(chemin, dpi=dpi, facecolor=SURFACE)
        chemins.append(chemin)
    return chemins
