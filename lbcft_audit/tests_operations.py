"""Bloc OPE — réexécution indépendante de scénarios de surveillance sur 100 % des opérations.

L'auditeur ne qualifie pas le soupçon : il identifie des schémas à risque et vérifie
si le dispositif de la banque les a détectés. Les exceptions sont ensuite qualifiées
sur pièces (anomalie avérée, faux positif, explication valide) puis transmises à la
fonction conformité, seule habilitée à déclarer à la CENTIF.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .donnees import Donnees
from .outils import ResultatTest, normaliser_adresse, normaliser_telephone
from .parametres import Parametres

BLOC = "Surveillance des opérations"


def _clients_alertes(d: Donnees) -> set[str]:
    return set(d.alertes["id_client"].dropna().astype(str))


def ope_01_fractionnement(d: Donnees, p: Parametres) -> ResultatTest:
    """Versements d'espèces juste sous le seuil de déclaration, rapprochés dans le temps."""
    seuil = float(p.seuils["declaration_especes_centif"])
    h = p.hypotheses["fractionnement"]
    fenetre = np.timedelta64(int(h["fenetre_jours"]), "D")
    ops = d.operations
    especes = ops[ops["type_operation"] == "VERSEMENT_ESPECES"]
    bande = especes[(especes["montant"] >= h["bande_basse"] * seuil) & (especes["montant"] < seuil)]
    bande = bande.sort_values(["id_client", "date_operation"])

    retenues, lignes = [], []
    for id_client, g in bande.groupby("id_client", sort=True):
        if len(g) < h["nb_min_versements"]:
            continue
        t = g["date_operation"].to_numpy()
        m = g["montant"].to_numpy(float)
        fin = np.searchsorted(t, t + fenetre, side="left")  # fenêtre [t_i ; t_i + N jours[
        cumul = np.concatenate([[0.0], np.cumsum(m)])
        nb = fin - np.arange(len(t))
        somme = cumul[fin] - cumul[np.arange(len(t))]
        debuts = np.flatnonzero((nb >= h["nb_min_versements"]) & (somme >= seuil))
        if debuts.size == 0:
            continue
        concernes = np.zeros(len(t), dtype=bool)
        for i in debuts:
            concernes[i : fin[i]] = True
        sel = g[concernes]
        retenues.append(sel)
        lignes.append(
            {
                "id_client": id_client,
                "nb_versements": len(sel),
                "montant_total": sel["montant"].sum(),
                "montant_moyen": round(float(sel["montant"].mean())),
                "nb_agences": sel["agence_operation"].nunique(),
                "nb_fenetres_7j": int(debuts.size),
                "premiere_date": sel["date_operation"].min(),
                "derniere_date": sel["date_operation"].max(),
            }
        )
    exceptions = pd.DataFrame(
        lignes,
        columns=[
            "id_client",
            "nb_versements",
            "montant_total",
            "montant_moyen",
            "nb_agences",
            "nb_fenetres_7j",
            "premiere_date",
            "derniere_date",
        ],
    )
    alertes = _clients_alertes(d)
    exceptions["alerte_banque"] = exceptions["id_client"].isin(alertes).map({True: "OUI", False: "NON"})
    detail = pd.concat(retenues) if retenues else especes.head(0)
    return ResultatTest(
        code="OPE-01",
        bloc=BLOC,
        titre="Fractionnement des versements d'espèces",
        objectif=(
            "Identifier les clients qui fractionnent leurs versements d'espèces juste sous le seuil "
            "de déclaration des transactions en espèces à la CENTIF."
        ),
        references="Loi uniforme LBC/FT/FP, art. 20, 21 et 72 ; Décision n°021 du 21/12/2023/CM/UMOA (seuil 15 M FCFA).",
        parametres={
            "seuil_declaration": int(seuil),
            "bande_basse": f"{h['bande_basse']:.0%} du seuil",
            "fenetre_jours": h["fenetre_jours"],
            "nb_min_versements": h["nb_min_versements"],
        },
        unite="clients",
        nb_population=int(especes["id_client"].nunique()),
        exceptions=exceptions,
        montant_exceptions=float(exceptions["montant_total"].sum()),
        detail=detail,
        commentaire=f"Population : {len(especes)} versements d'espèces de {especes['id_client'].nunique()} clients.",
    )


def ope_02_comptes_de_passage(d: Donnees, p: Parametres) -> ResultatTest:
    """Comptes de personnes physiques où des crédits importants ressortent en quelques jours."""
    h = p.hypotheses["compte_de_passage"]
    w = int(h["fenetre_jours"])
    ops = d.operations.merge(d.clients[["id_client", "type_client"]], on="id_client", how="left")
    ops = ops[ops["type_client"] == "PP"].copy()
    ops["jour"] = ops["date_operation"].dt.normalize()
    jour = ops.pivot_table(
        index=["id_compte", "id_client", "jour"], columns="sens", values="montant", aggfunc="sum", fill_value=0
    ).reset_index()
    for sens in ("C", "D"):
        if sens not in jour.columns:
            jour[sens] = 0

    lignes, retenus = [], []
    candidats = jour.loc[jour["C"] >= h["credits_min_journaliers"], "id_compte"].unique()
    for id_compte in candidats:
        g = jour[jour["id_compte"] == id_compte].sort_values("jour")
        jours = g["jour"].to_numpy()
        debits = np.concatenate([[0.0], np.cumsum(g["D"].to_numpy(float))])
        episodes, credits_ep, debits_ep, bloque_jusqu = [], 0.0, 0.0, None
        for i in np.flatnonzero(g["C"].to_numpy() >= h["credits_min_journaliers"]):
            if bloque_jusqu is not None and jours[i] < bloque_jusqu:
                continue
            fin = np.searchsorted(jours, jours[i] + np.timedelta64(w, "D"), side="left")
            sortie = debits[fin] - debits[i]
            credit = float(g["C"].iloc[i])
            if sortie >= h["taux_sortie_min"] * credit:
                episodes.append(jours[i])
                credits_ep += credit
                debits_ep += sortie
                bloque_jusqu = jours[i] + np.timedelta64(w, "D")
        if len(episodes) >= h["nb_episodes_min"]:
            lignes.append(
                {
                    "id_client": g["id_client"].iloc[0],
                    "id_compte": id_compte,
                    "nb_episodes": len(episodes),
                    "credits_episodes": credits_ep,
                    "debits_sous_3_jours": debits_ep,
                    "taux_sortie": debits_ep / credits_ep if credits_ep else np.nan,
                    "premier_episode": pd.Timestamp(min(episodes)),
                    "dernier_episode": pd.Timestamp(max(episodes)),
                }
            )
            retenus.append(id_compte)
    exceptions = pd.DataFrame(
        lignes,
        columns=[
            "id_client",
            "id_compte",
            "nb_episodes",
            "credits_episodes",
            "debits_sous_3_jours",
            "taux_sortie",
            "premier_episode",
            "dernier_episode",
        ],
    )
    exceptions["alerte_banque"] = exceptions["id_client"].isin(_clients_alertes(d)).map({True: "OUI", False: "NON"})
    detail = d.operations[d.operations["id_compte"].isin(retenus)]
    return ResultatTest(
        code="OPE-02",
        bloc=BLOC,
        titre="Comptes de passage (transit rapide des fonds)",
        objectif=(
            "Repérer les comptes de particuliers utilisés comme simples comptes de transit : "
            "crédits importants ressortis presque intégralement en quelques jours (profil de « mule »)."
        ),
        references="Loi uniforme LBC/FT/FP, art. 19 à 21 (vigilance constante, opérations inhabituelles).",
        parametres={
            "credits_min_journaliers": h["credits_min_journaliers"],
            "fenetre_jours": w,
            "taux_sortie_min": f"{h['taux_sortie_min']:.0%}",
            "nb_episodes_min": h["nb_episodes_min"],
            "perimetre": "personnes physiques",
        },
        unite="clients",
        nb_population=int(ops["id_compte"].nunique()),
        exceptions=exceptions,
        montant_exceptions=float(exceptions["credits_episodes"].sum()),
        detail=detail,
        commentaire="Périmètre limité aux personnes physiques (les entreprises paient leurs fournisseurs rapidement).",
    )


def ope_03_incoherence_profil(d: Donnees, p: Parametres) -> ResultatTest:
    """Crédits mensuels sans commune mesure avec le revenu ou le chiffre d'affaires déclaré."""
    h = p.hypotheses["incoherence_profil"]
    c = d.clients.set_index("id_client")
    reference = np.where(
        c["type_client"] == "PP",
        c["revenu_mensuel_declare"] * h["multiple_revenu_pp"],
        c["chiffre_affaires_annuel_declare"] / 12 * h["multiple_ca_mensuel_pm"],
    )
    reference = pd.Series(reference, index=c.index)
    credits = d.operations[d.operations["sens"] == "C"]
    mensuel = (
        credits.assign(mois=credits["date_operation"].dt.to_period("M"))
        .groupby(["id_client", "mois"], as_index=False)["montant"]
        .sum()
    )
    mensuel["plafond_profil"] = mensuel["id_client"].map(reference)
    sans_profil = mensuel.loc[mensuel["plafond_profil"].isna(), "id_client"].nunique()
    hors = mensuel[(mensuel["montant"] > mensuel["plafond_profil"]) & (mensuel["montant"] >= h["montant_min_mensuel"])]
    agr = (
        hors.groupby("id_client")
        .agg(
            nb_mois=("mois", "nunique"),
            credits_mois_concernes=("montant", "sum"),
            credit_mensuel_max=("montant", "max"),
        )
        .reset_index()
    )
    agr = agr[agr["nb_mois"] >= h["nb_mois_min"]]
    agr["type_client"] = agr["id_client"].map(c["type_client"])
    agr["profession_secteur"] = agr["id_client"].map(c["profession"].fillna(c["secteur_activite"]))
    agr["revenu_mensuel_ou_ca_mensuel"] = agr["id_client"].map(
        c["revenu_mensuel_declare"].fillna(c["chiffre_affaires_annuel_declare"] / 12)
    )
    agr["multiple_max"] = agr["credit_mensuel_max"] / agr["revenu_mensuel_ou_ca_mensuel"]
    agr["alerte_banque"] = agr["id_client"].isin(_clients_alertes(d)).map({True: "OUI", False: "NON"})
    colonnes = [
        "id_client",
        "type_client",
        "profession_secteur",
        "revenu_mensuel_ou_ca_mensuel",
        "nb_mois",
        "credit_mensuel_max",
        "multiple_max",
        "credits_mois_concernes",
        "alerte_banque",
    ]
    exceptions = agr[colonnes].sort_values("multiple_max", ascending=False).reset_index(drop=True)
    return ResultatTest(
        code="OPE-03",
        bloc=BLOC,
        titre="Flux incohérents avec le profil déclaré",
        objectif="Identifier les clients dont les crédits mensuels dépassent largement le revenu ou le CA déclaré.",
        references="Loi uniforme LBC/FT/FP, art. 19 à 21 (opérations inhabituelles au regard du profil) ; Instruction BCEAO n°003-03-2025.",
        parametres={
            "multiple_revenu_pp": h["multiple_revenu_pp"],
            "multiple_ca_mensuel_pm": h["multiple_ca_mensuel_pm"],
            "montant_min_mensuel": h["montant_min_mensuel"],
            "nb_mois_min": h["nb_mois_min"],
        },
        unite="clients",
        nb_population=int(mensuel["id_client"].nunique()),
        exceptions=exceptions,
        montant_exceptions=float(exceptions["credits_mois_concernes"].sum()),
        commentaire=(f"{sans_profil} client(s) non testable(s) faute de revenu ou de CA renseigné (voir KYC-01)."),
    )


def ope_04_reactivation(d: Donnees, p: Parametres) -> ResultatTest:
    """Comptes inactifs depuis plus d'un an réactivés par des mouvements importants."""
    h = p.hypotheses["reactivation"]
    comptes = d.comptes
    ops = d.operations.sort_values("date_operation")
    premiere = ops.groupby("id_compte")["date_operation"].min()
    c = comptes.assign(date_reprise=comptes["id_compte"].map(premiere))
    c = c[c["date_reprise"].notna() & c["date_dernier_mouvement_avant_periode"].notna()]
    c["jours_inactivite"] = (c["date_reprise"] - c["date_dernier_mouvement_avant_periode"]).dt.days
    dormants = c[c["jours_inactivite"] >= h["inactivite_min_jours"]]

    lignes = []
    for _, cpt in dormants.iterrows():
        fin = cpt["date_reprise"] + pd.Timedelta(days=int(h["fenetre_jours"]))
        f = ops[(ops["id_compte"] == cpt["id_compte"]) & (ops["date_operation"] < fin)]
        credits, debits = f.loc[f["sens"] == "C", "montant"].sum(), f.loc[f["sens"] == "D", "montant"].sum()
        if max(credits, debits) >= h["montant_min"]:
            lignes.append(
                {
                    "id_client": cpt["id_client"],
                    "id_compte": cpt["id_compte"],
                    "dernier_mouvement": cpt["date_dernier_mouvement_avant_periode"],
                    "date_reprise": cpt["date_reprise"],
                    "jours_inactivite": int(cpt["jours_inactivite"]),
                    "credits_30j": credits,
                    "debits_30j": debits,
                    "agence_compte": cpt["agence"],
                    "agences_operations": ", ".join(sorted(f["agence_operation"].dropna().unique())),
                }
            )
    exceptions = pd.DataFrame(
        lignes,
        columns=[
            "id_client",
            "id_compte",
            "dernier_mouvement",
            "date_reprise",
            "jours_inactivite",
            "credits_30j",
            "debits_30j",
            "agence_compte",
            "agences_operations",
        ],
    )
    exceptions["alerte_banque"] = exceptions["id_client"].isin(_clients_alertes(d)).map({True: "OUI", False: "NON"})
    return ResultatTest(
        code="OPE-04",
        bloc=BLOC,
        titre="Réactivation de comptes inactifs",
        objectif=(
            "Repérer les comptes inactifs depuis plus d'un an soudainement crédités puis débités de montants "
            "importants (risque de blanchiment et de fraude interne)."
        ),
        references="Loi uniforme LBC/FT/FP, art. 19 à 21 ; bonnes pratiques d'audit des comptes inactifs.",
        parametres={
            "inactivite_min_jours": h["inactivite_min_jours"],
            "fenetre_jours": h["fenetre_jours"],
            "montant_min": h["montant_min"],
        },
        unite="clients",
        nb_population=int(len(dormants)),
        exceptions=exceptions,
        montant_exceptions=float(exceptions["credits_30j"].sum()),
        commentaire=f"{len(dormants)} compte(s) réactivé(s) après au moins {h['inactivite_min_jours']} jours d'inactivité.",
    )


def ope_05_pays_a_risque(d: Donnees, p: Parametres) -> ResultatTest:
    """Transferts avec les pays listés par le GAFI et écarts avec la liste paramétrée par la banque."""
    listes = p["listes_gafi"]
    appel, surveillance = set(listes["appel_a_action"]), set(listes["surveillance_renforcee"])
    liste_banque = p.pays_liste_banque
    transferts = d.operations[d.operations["type_operation"].str.startswith("TRANSFERT")]
    exposes = transferts[transferts["pays_contrepartie"].isin(appel | surveillance)].copy()
    alertees = set(d.alertes["id_operation"].dropna())
    exposes["liste_gafi"] = np.where(
        exposes["pays_contrepartie"].isin(appel), "Appel à action", "Surveillance renforcée"
    )
    exposes["dans_liste_banque"] = exposes["pays_contrepartie"].isin(liste_banque).map({True: "OUI", False: "NON"})
    exposes["alerte_banque"] = exposes["id_operation"].isin(alertees).map({True: "OUI", False: "NON"})
    colonnes = [
        "id_operation",
        "date_operation",
        "id_client",
        "type_operation",
        "montant",
        "pays_contrepartie",
        "liste_gafi",
        "dans_liste_banque",
        "alerte_banque",
    ]
    exceptions = exposes.loc[exposes["alerte_banque"] == "NON", colonnes].reset_index(drop=True)

    # Écarts de paramétrage : pays manquants et pays obsolètes dans la liste de la banque
    gafi = appel | surveillance
    ecarts = pd.DataFrame(
        [
            {"pays": x, "ecart": "Listé par le GAFI, absent de la liste de la banque"}
            for x in sorted(gafi - liste_banque)
        ]
        + [
            {"pays": x, "ecart": "Présent dans la liste de la banque, retiré des listes du GAFI"}
            for x in sorted(liste_banque - gafi)
        ]
    )
    pay01 = d.alertes[d.alertes["scenario"] == "PAY-01"].merge(
        d.operations[["id_operation", "pays_contrepartie"]], on="id_operation", how="left"
    )
    obsoletes = pay01[pay01["pays_contrepartie"].isin(liste_banque - gafi)]
    par_pays = (
        exposes.groupby(["pays_contrepartie", "liste_gafi", "dans_liste_banque"])
        .agg(
            nb_transferts=("id_operation", "size"),
            montant=("montant", "sum"),
            nb_alertes=("alerte_banque", lambda s: int((s == "OUI").sum())),
        )
        .reset_index()
        .sort_values("montant", ascending=False)
    )
    return ResultatTest(
        code="OPE-05",
        bloc=BLOC,
        titre="Flux avec des pays à risque élevé (listes du GAFI)",
        objectif=(
            "Vérifier que les transferts avec les pays listés par le GAFI font l'objet d'une vigilance "
            "renforcée, et que la liste paramétrée dans l'outil de la banque est à jour."
        ),
        references=(
            "Loi uniforme LBC/FT/FP, art. 30 (pays présentant un risque plus élevé) ; "
            f"déclarations publiques du GAFI du {pd.Timestamp(listes['date_reference']):%d/%m/%Y}."
        ),
        parametres={
            "date_listes_gafi": listes["date_reference"],
            "date_maj_liste_banque": p["parametrage_banque"]["date_mise_a_jour_liste"],
        },
        unite="opérations",
        nb_population=int(len(exposes)),
        exceptions=exceptions,
        montant_exceptions=float(exceptions["montant"].sum()),
        annexes={
            "ecarts_liste": ecarts,
            "par_pays": par_pays,
            "alertes_pays_retires": obsoletes[["id_alerte", "id_client", "date_alerte", "pays_contrepartie"]],
        },
        commentaire=(
            f"{len(obsoletes)} alerte(s) PAY-01 portent sur des pays retirés des listes du GAFI "
            "(charge d'analyse inutile)."
        ),
    )


def ope_06_reseaux(d: Donnees, p: Parametres) -> ResultatTest:
    """Clients distincts partageant un même téléphone ou une même adresse (prête-noms, mules)."""
    taille_min = int(p.hypotheses["reseaux"]["taille_min_groupe"])
    c = d.clients[["id_client", "agence", "date_entree_relation", "telephone", "adresse"]].copy()
    c["tel_n"] = c["telephone"].map(normaliser_telephone)
    c["adr_n"] = c["adresse"].map(normaliser_adresse)
    debits = d.operations[(d.operations["sens"] == "D") & d.operations["contrepartie"].notna()]

    lignes, numero = [], 0
    for cle, libelle in (("tel_n", "téléphone"), ("adr_n", "adresse")):
        groupes = c[c[cle] != ""].groupby(cle)["id_client"].nunique()
        for valeur in groupes[groupes >= taille_min].index:
            numero += 1
            membres = c[c[cle] == valeur]
            flux = debits[debits["id_client"].isin(membres["id_client"])]
            commun = flux.groupby("contrepartie")["id_client"].nunique().sort_values(ascending=False)
            beneficiaire = commun.index[0] if len(commun) and commun.iloc[0] >= 2 else ""
            for _, m in membres.iterrows():
                vers = flux[(flux["id_client"] == m["id_client"]) & (flux["contrepartie"] == beneficiaire)]
                lignes.append(
                    {
                        "groupe": f"G{numero:02d}",
                        "identifiant_partage": libelle,
                        "id_client": m["id_client"],
                        "taille_groupe": len(membres),
                        "agence": m["agence"],
                        "date_entree_relation": m["date_entree_relation"],
                        "beneficiaire_commun": beneficiaire,
                        "montant_vers_beneficiaire": vers["montant"].sum(),
                    }
                )
    exceptions = pd.DataFrame(
        lignes,
        columns=[
            "groupe",
            "identifiant_partage",
            "id_client",
            "taille_groupe",
            "agence",
            "date_entree_relation",
            "beneficiaire_commun",
            "montant_vers_beneficiaire",
        ],
    )
    exceptions["alerte_banque"] = exceptions["id_client"].isin(_clients_alertes(d)).map({True: "OUI", False: "NON"})
    return ResultatTest(
        code="OPE-06",
        bloc=BLOC,
        titre="Réseaux de clients liés (identifiants partagés)",
        objectif=(
            "Détecter les groupes de clients distincts partageant un téléphone ou une adresse, signal "
            "possible de prête-noms ou de comptes de mules contrôlés par une même personne."
        ),
        references="Loi uniforme LBC/FT/FP, art. 20 (vigilance constante) ; Instruction BCEAO n°003-03-2025, art. 12 (bénéficiaires effectifs).",
        parametres={"taille_min_groupe": taille_min, "identifiants": "téléphone, adresse"},
        unite="clients",
        nb_population=int(len(c)),
        exceptions=exceptions,
        montant_exceptions=float(exceptions["montant_vers_beneficiaire"].sum()),
        commentaire="Les foyers (2 personnes à la même adresse) sont exclus par le seuil de taille de groupe.",
    )


TESTS_OPERATIONS = [
    ope_01_fractionnement,
    ope_02_comptes_de_passage,
    ope_03_incoherence_profil,
    ope_04_reactivation,
    ope_05_pays_a_risque,
    ope_06_reseaux,
]
