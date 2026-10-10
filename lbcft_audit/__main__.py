"""Ligne de commande : python -m lbcft_audit [generer | auditer | rapport | evaluer | tout]."""

from __future__ import annotations

import argparse
import sys

from .parametres import RACINE, charger_parametres


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        prog="python -m lbcft_audit",
        description="Audit du dispositif LBC/FT d'une banque de l'UMOA (données fictives).",
    )
    analyseur.add_argument(
        "commande",
        choices=["generer", "auditer", "rapport", "evaluer", "tout"],
        help="generer : données fictives ; auditer : tests + Excel ; rapport : rapport et "
        "graphiques ; evaluer : précision/rappel des tests ; tout : enchaîne les étapes",
    )
    analyseur.add_argument(
        "--parametres", help="chemin d'un fichier de paramètres YAML (défaut : config/parametres.yaml)"
    )
    args = analyseur.parse_args(argv)
    p = charger_parametres(args.parametres)

    # Accents et symboles corrects dans les consoles Windows
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")

    if args.commande in ("generer", "tout"):
        from .generation import ecrire_jeu_de_donnees

        dossier = ecrire_jeu_de_donnees(p)
        print(f"Données fictives écrites dans {dossier}")
        if args.commande == "generer":
            return 0

    from .moteur import executer_audit

    resultats = executer_audit(p=p)
    if args.commande in ("auditer", "tout"):
        from .export_excel import exporter_excel

        print("\nContrôles d'intégrité :", (resultats.integrite["statut"] == "ANOMALIE").sum(), "anomalie(s)")
        synthese = resultats.synthese()[["code", "test", "population", "exceptions"]]
        print(synthese.to_string(index=False))
        chemin = exporter_excel(resultats, p.dossier_sorties / "resultats_audit_lbcft.xlsx")
        print(f"\nFeuilles de travail Excel : {chemin}")
    if args.commande in ("rapport", "tout"):
        from .evaluation import charger_verite, evaluer
        from .graphiques import exporter_figures
        from .rapport import ecrire_rapport, generer_evaluation

        exporter_figures(resultats, RACINE / "docs" / "img")
        chemin = ecrire_rapport(resultats, RACINE / "docs" / "07_rapport_de_mission.md")
        print(f"Rapport de mission (projet) : {chemin}")
        verite = charger_verite(p.dossier_donnees)
        page = generer_evaluation(resultats, evaluer(resultats, verite), verite)
        (RACINE / "docs" / "08_evaluation_des_tests.md").write_text(page, encoding="utf-8")
        print(f"Évaluation des tests : {RACINE / 'docs' / '08_evaluation_des_tests.md'}")
    if args.commande in ("evaluer", "tout"):
        from .evaluation import charger_verite, evaluer

        evaluation = evaluer(resultats, charger_verite(p.dossier_donnees))
        print("\nÉvaluation des tests sur la vérité terrain du jeu fictif :")
        print(evaluation.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
