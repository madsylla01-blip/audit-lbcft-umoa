# 5. Programme de travail

Techniques : **ENT** entretien · **DOC** revue documentaire · **OBS** observation · **ADA** analyse de
données exhaustive · **RÉEX** réexécution · **ECH** test sur échantillon de pièces.

| Réf. | Objectif | Procédure d'audit détaillée | Source / données | Technique | Risque | Réf. FT |
|---|---|---|---|---|---|---|
| P01 | Comprendre le dispositif | Obtenir la politique LBC/FT, la cartographie des risques, l'organigramme de la conformité, les procédures de traitement des alertes et de déclaration ; mener un entretien avec le responsable de la conformité | Documents internes | ENT, DOC | Tous | — |
| P02 | Comprendre l'outil de surveillance | Obtenir la liste et le paramétrage des scénarios, la liste des pays à risque et sa date de mise à jour, le dernier rapport de revue annuelle de l'outil (Instr. 001-03-2025, art. 6) | Paramétrage de l'outil | DOC, OBS | R06, R07 | — |
| P03 | Obtenir des données fiables | Adresser la demande de données (7 tables), contrôler l'intégrité des extractions et rapprocher les totaux de la balance | Extractions du SI | ADA | Tous | Intégrité |
| P04 | Tester la détection des typologies | Rejouer les scénarios de fractionnement, comptes de passage, incohérence de profil, réactivation et réseaux sur 100 % des opérations | `operations`, `clients`, `comptes` | ADA, RÉEX | R06 | OPE-01 à OPE-04, OPE-06 |
| P05 | Mesurer la couverture de l'outil | Rapprocher les clients identifiés des alertes de la banque ; analyser le traitement des alertes de ces clients | `alertes` | ADA | R06 | COU-01 |
| P06 | Tester la vigilance sur les pays à risque | Comparer la liste paramétrée aux listes du GAFI en vigueur ; isoler les transferts non alertés et les alertes devenues sans objet | `operations`, paramétrage | ADA | R07 | OPE-05 |
| P07 | Tester le filtrage | Rejouer le filtrage de toute la clientèle avec une comparaison approchée ; qualifier chaque correspondance (date de naissance, pièces) | `clients`, `liste_sanctions` | ADA, ECH | R08 | FIL-01 |
| P08 | Tester les DTE | Recalculer les DTE attendues (cumul journalier ≥ 15 M FCFA) et les rapprocher du registre | `operations`, `declarations_especes` | ADA | R11 | DEC-01 |
| P09 | Tester le traitement des alertes | Mesurer l'arriéré et son ancienneté ; isoler les clôtures sans motif et les clôtures en masse ; revoir un échantillon de rapports d'analyse | `alertes`, dossiers d'analyse | ADA, ECH | R09 | ALE-01, ALE-02 |
| P10 | Tester les délais de déclaration | Mesurer les délais alerte → décision → transmission ; vérifier les accusés de réception de la CENTIF sur un échantillon | `declarations_soupcon`, accusés | ADA, ECH | R10 | ALE-03 |
| P11 | Tester la qualité KYC | Mesurer la complétude des champs obligatoires, les pièces expirées, les revues en retard, les BE manquants ; vérifier un échantillon de dossiers physiques | `clients`, dossiers | ADA, ECH | R01, R02, R05 | KYC-01, KYC-02, KYC-03, KYC-05 |
| P12 | Tester les PPE et la classification | Vérifier l'approbation de la haute direction, la classification et la réévaluation des PPE ; recalculer la cohérence des niveaux de risque | `clients`, `operations` | ADA, ECH | R03, R04 | KYC-04, KYC-06 |
| P13 | Tester la confidentialité des DS | Revoir les habilitations au registre des DS et la procédure de confidentialité | Habilitations | DOC, ENT | R12 | — |
| P14 | Tester la formation | Vérifier le programme annuel, les listes de présence et les évaluations post-formation | Registres de formation | DOC, ECH | R13 | — |
| P15 | Qualifier les exceptions | Vérifier sur pièces un échantillon priorisé d'exceptions ; documenter la qualification ; transmettre les cas potentiellement suspects à la conformité | Exceptions, dossiers | ECH | Tous | Priorisation |
| P16 | Conclure | Rédiger les constats 5C, valider les faits avec les audités, tenir la réunion de clôture, finaliser le rapport et le plan d'action | Feuilles de travail | — | Tous | Rapport |

**Échantillonnage des tests sur pièces.** Tirage aléatoire reproductible (graine documentée), stratifié par
montant lorsque la population est hétérogène ; à défaut de méthodologie interne, 25 à 60 éléments pour un
contrôle exécuté plusieurs fois par jour (traitement des alertes), 20 à 40 pour un contrôle quotidien.
