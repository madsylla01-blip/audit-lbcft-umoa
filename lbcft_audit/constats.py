"""Rédaction des constats au format 5C à partir des résultats chiffrés.

Les faits (« Constat ») sont calculés ; les causes sont PRÉSUMÉES et doivent être
confirmées en entretien ; les recommandations sont des propositions. L'ensemble est
un projet soumis au jugement de l'auditeur et à la validation des audités.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .moteur import ResultatsAudit
from .outils import accord, decimal_fr, fcfa, nom_pays, nombre, pourcentage

ECHEANCES = {"Critique": "Immédiate (< 1 mois)", "Majeur": "3 mois", "Modéré": "6 mois", "Faible": "12 mois"}
ORDRE = {"Critique": 0, "Majeur": 1, "Modéré": 2, "Faible": 3}


@dataclass
class Constat:
    numero: str
    titre: str
    notation: str
    tests: list[str]
    critere: str
    constat: str
    cause: str
    consequence: str
    recommandation: str
    responsable: str

    @property
    def echeance(self) -> str:
        return ECHEANCES[self.notation]


def _liste(valeurs) -> str:
    valeurs = [str(v) for v in valeurs]
    return ", ".join(valeurs) if valeurs else "aucun"


def rediger_constats(r: ResultatsAudit) -> list[Constat]:
    p, d = r.parametres, r.donnees
    constats: list[Constat] = []
    arrete = f"{p.date_arrete:%d/%m/%Y}"

    # C1 — Filtrage des sanctions -------------------------------------------------
    fil = r["FIL-01"].exceptions
    if len(fil):
        fortes = fil[fil["qualification"].str.startswith("Correspondance forte")]
        homonymes = fil[~fil.index.isin(fortes.index)]
        exemples = " ; ".join(
            f"client {x.id_client} / entrée {x.id_entree_liste} (score {decimal_fr(x.score_similarite)})"
            for x in fortes.head(3).itertuples()
        )
        constats.append(
            Constat(
                numero="",
                titre="Correspondances avec la liste de sanctions non détectées par le filtrage",
                notation="Critique",
                tests=["FIL-01"],
                critere=(
                    "Le système d'information doit permettre le filtrage des clients et la prise en compte « sans "
                    "délai » des mesures de sanctions financières ciblées (Instruction BCEAO n°001-03-2025, art. 6 ; "
                    "recommandation 6 du GAFI)."
                ),
                constat=(
                    f"Le rejeu du filtrage de {nombre(len(d.clients))} clients avec une comparaison approchée fait "
                    f"ressortir {accord(len(fil), 'correspondance')} : {accord(len(fortes), 'forte', 'fortes')} (nom "
                    f"et date de naissance identiques, ou raison sociale identique hors forme juridique) et "
                    f"{accord(len(homonymes), 'homonymie probable', 'homonymies probables')} à lever. Aucune n'a été "
                    f"signalée par l'outil de la banque. Exemples : {exemples}."
                ),
                cause=(
                    "Cause présumée, à confirmer avec la DSI et l'éditeur : comparaison exacte des noms, sans "
                    "normalisation des accents, de l'ordre des mots ni des formes juridiques."
                ),
                consequence=(
                    "Risque d'entrer ou de rester en relation, et d'exécuter des opérations, avec des personnes "
                    "ou entités visées par des mesures de gel des avoirs : sanctions et atteinte grave à la "
                    "réputation."
                ),
                recommandation=(
                    f"Traiter sans délai {'la correspondance forte' if len(fortes) == 1 else f'les {len(fortes)} correspondances fortes'} selon la procédure de "
                    "gel des avoirs et documenter la levée des homonymies ; paramétrer une recherche "
                    "approchée (seuil calibré) ; tester le filtrage avec un jeu de cas de contrôle à chaque "
                    "mise à jour de l'outil ou des listes."
                ),
                responsable="Responsable de la conformité ; DSI",
            )
        )

    # C2 — Couverture du dispositif ------------------------------------------------
    cou = r["COU-01"]
    par_test = cou.annexes["couverture_par_test"].set_index("test")
    ensemble = par_test.loc["Ensemble"]
    traitement = cou.annexes["traitement_banque"].set_index("traitement")["nb_clients"]
    sans_suite = int(traitement.get("Alerte(s) classée(s) sans suite", 0))
    scenarios = ", ".join(p["parametrage_banque"]["scenarios"])
    lignes_tests = " ; ".join(
        f"{code} : {int(x.clients_identifies - x.clients_avec_alerte)} sur {int(x.clients_identifies)} sans alerte"
        for code, x in par_test.drop(index="Ensemble").iterrows()
    )
    constats.append(
        Constat(
            numero="",
            titre="Schémas à risque non couverts par le dispositif de surveillance",
            notation="Critique",
            tests=["COU-01", "OPE-01", "OPE-02", "OPE-03", "OPE-04", "OPE-06"],
            critere=(
                "Le dispositif doit assurer le profilage des clients, le suivi des mouvements avec génération "
                "d'alertes et l'identification des opérations suspectes ; il est révisé au moins une fois par an "
                "(Instruction BCEAO n°001-03-2025, art. 6). Les opérations inhabituelles font l'objet d'un examen "
                "particulier (Loi uniforme LBC/FT/FP, art. 20 et 21)."
            ),
            constat=(
                f"Les scénarios rejoués par l'audit sur 100 % des {nombre(len(d.operations))} opérations identifient "
                f"{int(ensemble.clients_identifies)} clients présentant des schémas à risque. "
                f"{nombre(cou.nb_exceptions)} d'entre eux "
                f"({pourcentage(cou.nb_exceptions, ensemble.clients_identifies)}) n'ont déclenché aucune alerte sur "
                f"12 mois ({lignes_tests}). {accord(sans_suite, 'autre client', 'autres clients')} n'{'a' if sans_suite < 2 else 'ont'} "
                f"eu que des alertes classées sans suite. L'outil comporte {len(p['parametrage_banque']['scenarios'])} scénarios ({scenarios}) et "
                "aucun scénario de fractionnement, de transit rapide, de réactivation de compte inactif ni "
                "d'identifiants partagés."
            ),
            cause=(
                "Cause présumée : scénarios fondés sur des seuils unitaires ; absence de revue annuelle documentée "
                "de leur pertinence et de leur couverture des typologies."
            ),
            consequence=(
                "Opérations suspectes non détectées et non déclarées à la CENTIF (Loi uniforme, art. 60) ; "
                "exposition au blanchiment et aux sanctions de la Commission Bancaire."
            ),
            recommandation=(
                f"Transmettre sans délai à la conformité la liste priorisée des "
                f"{int(ensemble.clients_identifies)} clients pour analyse et, le cas échéant, déclaration ; "
                "compléter l'outil par des scénarios couvrant ces typologies ; instaurer une revue annuelle "
                "de l'efficacité des scénarios (taux d'alertes pertinentes, tests de couverture)."
            ),
            responsable="Responsable de la conformité ; Direction des risques ; DSI",
        )
    )

    # C3 — Liste des pays à risque -------------------------------------------------
    ope5 = r["OPE-05"]
    ecarts = ope5.annexes["ecarts_liste"]
    manquants = [nom_pays(x) for x in ecarts.loc[ecarts["ecart"].str.startswith("Listé"), "pays"]]
    obsoletes = [nom_pays(x) for x in ecarts.loc[ecarts["ecart"].str.startswith("Présent"), "pays"]]
    pays_ex = sorted(nom_pays(x) for x in ope5.exceptions["pays_contrepartie"].unique())
    constats.append(
        Constat(
            numero="",
            titre="Liste des pays à risque non mise à jour dans l'outil de surveillance",
            notation="Majeur",
            tests=["OPE-05"],
            critere=(
                "Les relations et opérations avec les pays présentant un risque plus élevé font l'objet d'une "
                "vigilance renforcée (Loi uniforme LBC/FT/FP, art. 30), sur la base des déclarations publiques du "
                f"GAFI (dernière en date : {pd.Timestamp(p['listes_gafi']['date_reference']):%d/%m/%Y})."
            ),
            constat=(
                f"La liste paramétrée (mise à jour le "
                f"{pd.Timestamp(p['parametrage_banque']['date_mise_a_jour_liste']):%d/%m/%Y}) omet "
                f"{len(manquants)} pays listés par le GAFI ({_liste(manquants)}) et conserve {len(obsoletes)} pays "
                f"retirés des listes ({_liste(obsoletes)}). Effets mesurés : {accord(ope5.nb_exceptions, 'transfert')} "
                f"({fcfa(ope5.montant_exceptions)}) avec {_liste(pays_ex)} sans aucune alerte ; "
                f"{accord(len(ope5.annexes['alertes_pays_retires']), 'alerte générée', 'alertes générées')} sur des "
                "pays retirés."
            ),
            cause="Cause présumée : pas de procédure de mise à jour de la liste après chaque plénière du GAFI.",
            consequence=(
                "Vigilance renforcée non appliquée à des flux à risque ; charge d'analyse consommée par des "
                "alertes devenues sans objet."
            ),
            recommandation=(
                "Mettre la liste à jour ; formaliser sa révision après chaque plénière du GAFI (février, "
                "juin, octobre) avec un contrôle de second niveau ; revoir a posteriori les transferts "
                "non alertés."
            ),
            responsable="Responsable de la conformité",
        )
    )

    # C4 — Déclarations de transactions en espèces ----------------------------------
    dec = r["DEC-01"]
    if dec.nb_exceptions:
        ag = dec.annexes["par_agence"].iloc[0]
        constats.append(
            Constat(
                numero="",
                titre="Déclarations de transactions en espèces (DTE) non transmises",
                notation="Majeur",
                tests=["DEC-01"],
                critere=(
                    "Les transactions en espèces d'un montant au moins égal à 15 M FCFA, en une ou plusieurs "
                    "opérations liées, sont déclarées à la CENTIF (Loi uniforme LBC/FT/FP, art. 72 ; Décision "
                    "n°021 du 21/12/2023/CM/UMOA)."
                ),
                constat=(
                    f"{dec.nb_population} DTE étaient attendues sur la période (cumul journalier par client et par "
                    f"sens). {dec.nb_exceptions} {'est absente' if dec.nb_exceptions < 2 else 'sont absentes'} du "
                    f"registre ({fcfa(dec.montant_exceptions)}). L'agence {ag.agence} concentre "
                    f"{accord(int(ag.dte_manquantes), 'omission')}, soit "
                    f"{pourcentage(ag.dte_manquantes, ag.dte_attendues)} de ses DTE attendues."
                ),
                cause="Cause présumée : identification manuelle des DTE en agence, sans contrôle de second niveau.",
                consequence="Manquement à une obligation déclarative ; sanctions de l'autorité de supervision.",
                recommandation=(
                    "Régulariser les déclarations manquantes ; automatiser la détection des DTE (y compris "
                    "les opérations liées) ; contrôle mensuel d'exhaustivité par la conformité."
                ),
                responsable="Responsable de la conformité ; Direction du réseau d'agences",
            )
        )

    # C5 — Traitement des alertes ---------------------------------------------------
    a1, a2 = r["ALE-01"], r["ALE-02"]
    if a1.nb_exceptions or a2.nb_exceptions:
        ouvertes = int((d.alertes["statut"] == "OUVERTE").sum())
        plus_180 = int((a1.exceptions["age_jours"] > 180).sum())
        top = a1.annexes["par_analyste"].sort_values("en_souffrance", ascending=False).iloc[0]
        sans_motif = int(a2.exceptions["anomalie"].str.contains("sans motif", case=False).sum())
        journees = a2.annexes["journees_de_cloture_massive"]
        detail_j = " ; ".join(
            f"{x.jour_cloture:%d/%m/%Y} : {x.nb_clotures} clôtures par l'analyste {x.analyste}"
            for x in journees.itertuples()
        )
        massives = int(a2.exceptions["anomalie"].str.contains("masse").sum())
        constats.append(
            Constat(
                numero="",
                titre="Arriéré d'alertes et clôtures non justifiées",
                notation="Majeur",
                tests=["ALE-01", "ALE-02"],
                critere=(
                    "Les opérations inhabituelles sont examinées et l'examen est consigné dans un rapport écrit "
                    "confidentiel, conservé dix ans (Loi uniforme LBC/FT/FP, art. 21 et 23) ; délai interne de "
                    f"traitement : {p.hypotheses['alertes']['delai_max_traitement_jours']} jours."
                ),
                constat=(
                    f"{ouvertes} alertes étaient ouvertes au {arrete}, dont {a1.nb_exceptions} hors délai "
                    f"({plus_180} de plus de 180 jours) ; l'analyste {top.analyste} en porte {int(top.en_souffrance)}. "
                    f"{accord(sans_motif, 'alerte')} {'a' if sans_motif < 2 else 'ont'} été clôturée"
                    f"{'' if sans_motif < 2 else 's'} sans motif et {massives} clôturées en masse ({detail_j})."
                ),
                cause=(
                    "Cause présumée : effectif d'analyse insuffisant et absence de supervision de la file d'alertes "
                    "et des clôtures."
                ),
                consequence="Soupçons non examinés ou examinés superficiellement ; absence de preuve de l'analyse.",
                recommandation=(
                    "Apurer l'arriéré par ordre d'ancienneté ; rendre le motif de clôture obligatoire ; "
                    "faire revoir par échantillon les clôtures par un superviseur ; suivre mensuellement "
                    "l'arriéré en comité."
                ),
                responsable="Responsable de la conformité",
            )
        )

    # C6 — Délais des déclarations de soupçon ---------------------------------------
    a3 = r["ALE-03"]
    if a3.nb_exceptions:
        ds = a3.annexes["distribution_delais"]
        h = p.hypotheses["declarations_soupcon"]
        nb_analyse = int(a3.exceptions["anomalie"].str.contains("Analyse").sum())
        nb_transmission = int(a3.exceptions["anomalie"].str.contains("ransmission").sum())
        constats.append(
            Constat(
                numero="",
                titre="Délais excessifs d'analyse et de transmission des déclarations de soupçon",
                notation="Majeur",
                tests=["ALE-03"],
                critere=(
                    "La déclaration de soupçon est faite « immédiatement » à la CENTIF (Loi uniforme LBC/FT/FP, "
                    f"art. 60 et 61) ; critères d'audit retenus : analyse en {h['delai_max_analyse_jours']} jours, "
                    f"transmission en {h['delai_max_transmission_jours']} jours après la décision."
                ),
                constat=(
                    f"Sur {a3.nb_population} déclarations de la période, {nb_analyse} ont été décidées plus de "
                    f"{h['delai_max_analyse_jours']} jours après l'alerte (maximum : "
                    f"{int(ds['delai_analyse_jours'].max())} jours) et {nb_transmission} transmises plus de "
                    f"{h['delai_max_transmission_jours']} jours après la décision (maximum : "
                    f"{int(ds['delai_transmission_jours'].max())} jours)."
                ),
                cause="Cause présumée : absence de délai formalisé et de suivi des déclarations en cours.",
                consequence="Efficacité réduite des investigations de la CENTIF ; risque de sanction.",
                recommandation=(
                    "Fixer dans la procédure des délais maximaux d'analyse et de transmission ; transmettre "
                    "le jour de la décision ; suivre les délais en comité."
                ),
                responsable="Responsable de la conformité (correspondant CENTIF)",
            )
        )

    # C7 — PPE -------------------------------------------------------------------------
    k4 = r["KYC-04"]
    if k4.nb_exceptions:
        synth = k4.annexes["synthese_anomalies"].set_index("anomalie")["nb_ppe"]
        constats.append(
            Constat(
                numero="",
                titre="Mesures de vigilance renforcée incomplètes sur les PPE",
                notation="Majeur",
                tests=["KYC-04"],
                critere=(
                    "L'entrée en relation avec une PPE est autorisée par la haute direction ; l'origine du patrimoine "
                    "et des fonds est établie ; le profil est réévalué au moins tous les trois ans (Loi uniforme "
                    "LBC/FT/FP, art. 29)."
                ),
                constat=(
                    f"Sur {k4.nb_population} PPE, {k4.nb_exceptions} présentent au moins une anomalie : "
                    f"{int(synth.iloc[0])} sans approbation de la haute direction, {int(synth.iloc[1])} non "
                    f"classées à risque élevé, {int(synth.iloc[2])} non réévaluées depuis plus de trois ans."
                ),
                cause="Cause présumée : absence de contrôle bloquant à l'ouverture et de suivi des échéances de revue.",
                consequence="Vigilance renforcée non appliquée à des clients exposés au risque de corruption.",
                recommandation=(
                    "Régulariser les dossiers ; rendre l'approbation de la haute direction bloquante dans le "
                    "workflow d'ouverture ; suivre les échéances de réévaluation des PPE."
                ),
                responsable="Responsable de la conformité ; Direction de la clientèle",
            )
        )

    # C8 — Qualité des dossiers KYC ----------------------------------------------------
    k1, k2, k3, k5, k6 = (r[c] for c in ("KYC-01", "KYC-02", "KYC-03", "KYC-05", "KYC-06"))
    ag = k1.annexes["par_agence"].iloc[0]
    constats.append(
        Constat(
            numero="",
            titre="Dossiers clients incomplets, échus ou mal classés",
            notation="Majeur",
            tests=["KYC-01", "KYC-02", "KYC-03", "KYC-05", "KYC-06"],
            critere=(
                "Identification et vérification de l'identité sur pièce en cours de validité, identification du "
                "bénéficiaire effectif des personnes morales (seuil de 25 %), mise à jour des informations et "
                "classification fondée sur les risques (Instruction BCEAO n°003-03-2025, art. 5 à 12 ; Loi "
                "uniforme LBC/FT/FP, art. 6, 15, 19 et 25)."
            ),
            constat=(
                f"{k1.nb_exceptions} dossiers présentent au moins un champ obligatoire vide (agence {ag.agence} : "
                f"{pourcentage(ag.taux_incomplets, 1)} de ses clients) ; {k2.nb_exceptions} clients ont une pièce "
                f"d'identité expirée ; {k3.nb_exceptions} revues périodiques sont en retard ; {k5.nb_exceptions} "
                f"personnes morales n'ont pas de bénéficiaire effectif identifié ; {k6.nb_exceptions} clients ont "
                "une classification incohérente avec leurs facteurs de risque."
            ),
            cause="Cause présumée : contrôles de saisie non bloquants et absence de campagne de mise à jour des dossiers.",
            consequence=(
                "Connaissance client insuffisante, qui fragilise toute la surveillance (profils de référence "
                "erronés ou absents) ; relations maintenues sans vigilance satisfaisante (art. 25)."
            ),
            recommandation=(
                "Lancer une campagne de mise à jour priorisée par le risque, en commençant par l'agence "
                f"{ag.agence} ; rendre bloquants les champs obligatoires ; recalculer la classification à "
                "partir des facteurs de risque."
            ),
            responsable="Direction du réseau d'agences ; Responsable de la conformité",
        )
    )

    constats.sort(key=lambda c: ORDRE[c.notation])
    for i, c in enumerate(constats, start=1):
        c.numero = f"C{i}"
    return constats


def opinion(constats: list[Constat]) -> str:
    notations = [c.notation for c in constats]
    if "Critique" in notations:
        return "Insuffisant"
    if notations.count("Majeur") >= 2:
        return "À améliorer"
    if notations:
        return "Globalement satisfaisant"
    return "Satisfaisant"


def points_forts(r: ResultatsAudit) -> list[str]:
    """Constats positifs mesurés (une opinion équilibrée les mentionne)."""
    d, p = r.donnees, r.parametres
    forts = []
    anomalies = int((r.integrite["statut"] == "ANOMALIE").sum())
    if anomalies == 0:
        forts.append(
            "Les extractions sont intègres : aucune anomalie de clé, de période ni de cohérence "
            "comptes / clients (totaux restant à rapprocher de la comptabilité)."
        )
    esp = d.operations[
        (d.operations["type_operation"] == "VERSEMENT_ESPECES")
        & (d.operations["montant"] >= p.seuils["declaration_especes_centif"])
    ]
    alertes_op = set(d.alertes["id_operation"].dropna())
    if len(esp):
        forts.append(
            f"Les versements d'espèces unitaires d'au moins 15 M FCFA sont alertés : "
            f"{pourcentage(esp['id_operation'].isin(alertes_op).sum(), len(esp))} des {len(esp)} cas."
        )
    appel = set(p["listes_gafi"]["appel_a_action"])
    tr = d.operations[d.operations["pays_contrepartie"].isin(appel)]
    if len(tr):
        forts.append(
            f"Les transferts avec les pays faisant l'objet d'un appel à action du GAFI sont alertés : "
            f"{pourcentage(tr['id_operation'].isin(alertes_op).sum(), len(tr))} des {len(tr)} cas."
        )
    dec = r["DEC-01"]
    forts.append(
        f"{pourcentage(dec.nb_population - dec.nb_exceptions, dec.nb_population)} des DTE attendues "
        "figurent au registre des déclarations."
    )
    return forts
