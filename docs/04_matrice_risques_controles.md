# 4. Matrice risques / contrôles

Processus audité : **dispositif LBC/FT** (conformité, réseau d'agences, DSI). Risque inhérent noté de 1
(faible) à 4 (élevé) = probabilité × impact, ramené sur 4. Les résultats renvoient aux constats du rapport
(`07_rapport_de_mission.md`) obtenus sur la banque fictive.

| Réf. | Risque | Référence | Contrôle clé attendu | Nature · mode | Propriétaire | Test d'audit | Risque inhérent | Résultat (BFU fictive) |
|---|---|---|---|---|---|---|---|---|
| R01 | Entrée ou maintien en relation sans identification et vérification complètes | LU art. 16, 17, 19 ; Instr. 003-03-2025 art. 5 à 8 | Champs obligatoires bloquants ; contrôle de second niveau des ouvertures ; relance des pièces échues | Préventif · automatique et manuel | Réseau d'agences ; conformité | KYC-01, KYC-02 | 3 | Déficient (C8) |
| R02 | Bénéficiaire effectif des personnes morales non identifié | Instr. 003-03-2025 art. 12 ; LU art. 25 | Identification du BE (seuil de 25 %) avant ouverture ; consultation du registre | Préventif · manuel | Réseau d'agences | KYC-05 | 3 | Déficient (C8) |
| R03 | PPE non identifiée ou sans vigilance renforcée | LU art. 29 | Approbation de la haute direction ; origine des fonds ; classement à risque élevé ; réévaluation triennale | Préventif · manuel | Conformité ; direction générale | KYC-04 | 4 | Déficient (C7) |
| R04 | Classification des risques ne reflétant pas les facteurs de risque | LU art. 6 et 15 ; Instr. 001-03-2025 | Calcul automatique du niveau de risque à partir des facteurs (PPE, BE, pays, activité) | Préventif · automatique | Conformité | KYC-06 | 3 | Déficient (C8) |
| R05 | Profils clients non mis à jour (référence de surveillance faussée) | LU art. 19 | Revue périodique selon le niveau de risque, suivie par un tableau de bord | Détectif · manuel | Réseau d'agences ; conformité | KYC-03 | 3 | Déficient (C8) |
| R06 | Opérations suspectes non détectées faute de scénario adapté | LU art. 20 et 21 ; Instr. 001-03-2025 art. 6 | Scénarios couvrant les typologies de la cartographie ; revue annuelle de leur efficacité | Détectif · automatique | Conformité ; DSI | OPE-01 à OPE-04, OPE-06, COU-01 | 4 | Déficient (C2) |
| R07 | Flux avec des pays à risque sans vigilance renforcée | LU art. 30 ; listes du GAFI | Liste des pays mise à jour après chaque plénière du GAFI, contrôlée en second niveau | Préventif · manuel | Conformité | OPE-05 | 3 | Déficient (C3) |
| R08 | Relation ou opération avec une personne visée par une mesure de gel | Instr. 001-03-2025 art. 6 ; recommandation 6 du GAFI | Filtrage approché des clients et des opérations, mise à jour sans délai, tests périodiques du filtrage | Préventif · automatique | Conformité ; DSI | FIL-01 | 4 | Déficient (C1) |
| R09 | Alertes non traitées, ou clôturées sans analyse documentée | LU art. 21 et 23 | Délai de traitement ; motif obligatoire ; revue des clôtures par un superviseur | Détectif · manuel | Conformité | ALE-01, ALE-02 | 4 | Déficient (C5) |
| R10 | Déclaration de soupçon tardive ou absente | LU art. 60 et 61 | Délais formalisés ; suivi des dossiers en cours ; transmission le jour de la décision | Détectif · manuel | Correspondant CENTIF | ALE-03 | 4 | Déficient (C6) |
| R11 | Transaction en espèces ≥ 15 M FCFA non déclarée | LU art. 72 ; Décision n°021/2023 | Détection automatique des DTE (opérations liées comprises) et contrôle d'exhaustivité mensuel | Détectif · automatique | Conformité ; agences | DEC-01 | 3 | Déficient (C4) |
| R12 | Divulgation de l'existence d'une déclaration de soupçon | LU art. 63 | Accès restreint au registre des DS ; sensibilisation du personnel | Préventif · manuel | Conformité | Entretien ; revue des habilitations | 3 | Non testé (hors analyse de données) |
| R13 | Personnel insuffisamment formé | Instr. 001-03-2025 art. 9 et 10 | Programme annuel de formation, évaluation post-formation | Préventif · manuel | RH ; conformité | Revue documentaire | 2 | Non testé |
| R14 | Documents non conservés pendant la durée légale | LU art. 23 | Archivage 10 ans des dossiers clients, opérations et rapports d'analyse | Préventif · manuel | Conformité ; logistique | Échantillon de dossiers anciens | 2 | Non testé |

**Légende.** LU : loi uniforme LBC/FT/FP de 2023. BFU : Banque Fictive de l'Union. Les risques R12 à R14
relèvent de tests sur pièces ou d'entretiens : ils figurent dans le programme de travail mais pas dans
l'analyse de données.
