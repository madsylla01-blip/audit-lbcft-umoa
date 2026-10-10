# 6. Catalogue des tests

Chaque test est une fonction Python documentée (`lbcft_audit/tests_*.py`) qui renvoie : population testée,
exceptions, montant concerné, paramètres et références. Les paramètres sont dans `config/parametres.yaml` ;
ceux qui relèvent du jugement de l'auditeur sont marqués « hypothèse ».

---

## Bloc OPE — Surveillance des opérations (réexécution indépendante)

### OPE-01 — Fractionnement des versements d'espèces

- **Question.** Des clients fractionnent-ils leurs versements pour rester sous le seuil de déclaration ?
- **Logique.** Versements d'espèces compris entre 70 % et 100 % du seuil de 15 M FCFA ; pour chaque client,
  fenêtre glissante de 7 jours ; exception si au moins 3 versements dans la fenêtre et cumul ≥ 15 M FCFA.
- **Paramètres.** Seuil 15 M FCFA (Décision n°021/2023) ; bande basse 70 %, fenêtre 7 jours, 3 versements
  (hypothèses).
- **Sortie.** Par client : nombre et montant des versements concernés, nombre d'agences utilisées,
  première et dernière date, existence d'une alerte de la banque.
- **Faux positifs.** Commerces à forte recette saisonnière : à lever au vu du chiffre d'affaires.
- **Limites.** Un fractionnement plus fin (versements bien inférieurs à 70 % du seuil) échappe au test : le
  compléter par OPE-03.

### OPE-02 — Comptes de passage (transit rapide des fonds)

- **Question.** Des comptes de particuliers servent-ils de simple transit ?
- **Logique.** Par compte et par jour : crédits ≥ 10 M FCFA, puis débits sur 3 jours ≥ 90 % de ces crédits =
  un épisode ; exception à partir de 3 épisodes sur la période.
- **Paramètres.** 10 M FCFA, 3 jours, 90 %, 3 épisodes (hypothèses).
- **Limites.** Restreint aux personnes physiques : les entreprises paient leurs fournisseurs rapidement,
  ce qui produirait trop de faux positifs ; un test dédié serait nécessaire pour elles.

### OPE-03 — Flux incohérents avec le profil déclaré

- **Question.** Les montants reçus sont-ils cohérents avec le revenu ou le chiffre d'affaires déclaré ?
- **Logique.** Crédits mensuels > 5 × revenu mensuel (personnes physiques) ou > 3 × CA mensuel (personnes
  morales), et ≥ 5 M FCFA ; exception si au moins 2 mois concernés.
- **Limites.** Les clients sans revenu ni CA renseigné ne sont pas testables : ils sont comptés en
  commentaire et relèvent de KYC-01. Faux positifs typiques : cession d'un bien, indemnité, sinistre
  (justificatif à obtenir).

### OPE-04 — Réactivation de comptes inactifs

- **Question.** Des comptes dormants sont-ils soudainement utilisés pour des montants importants ?
- **Logique.** Comptes dont le dernier mouvement avant la période date d'au moins 365 jours ; première
  opération de la période = réactivation ; exception si les crédits ou les débits des 30 jours suivants
  atteignent 5 M FCFA. Les agences des opérations sont restituées (une réactivation dans une autre agence
  que celle du compte est un signal de fraude interne).
- **Liens.** Utile aussi à l'audit de la fraude interne (détournement de comptes dormants).

### OPE-05 — Flux avec des pays à risque élevé

- **Question.** Les transferts avec les pays listés par le GAFI font-ils l'objet d'une vigilance
  renforcée, et la liste de l'outil est-elle à jour ?
- **Logique.** Transferts internationaux avec un pays des listes du GAFI (appel à action et surveillance
  renforcée) ; exception = transfert sans alerte. Annexe : écarts entre la liste de la banque et celles du
  GAFI (pays manquants, pays retirés) et alertes générées sur des pays retirés.
- **Référence.** Loi uniforme, art. 30 ; déclarations publiques du GAFI du 19 juin 2026.

### OPE-06 — Réseaux de clients liés

- **Question.** Des clients distincts partagent-ils un téléphone ou une adresse (prête-noms, mules) ?
- **Logique.** Normalisation des téléphones (8 derniers chiffres) et des adresses (minuscules, sans accents
  ni ponctuation) ; groupes d'au moins 3 clients ; recherche d'un bénéficiaire commun des fonds débités.
- **Faux positifs.** Membres d'un même foyer : à lever avec un justificatif de domicile.

### COU-01 — Couverture du dispositif de surveillance

- **Question.** Les clients identifiés par OPE-01 à OPE-06 ont-ils déclenché au moins une alerte de la
  banque sur la période ?
- **Sortie.** Taux de couverture par test et global ; traitement des alertes de ces clients (aucune alerte,
  classées sans suite, en cours, déclaration de soupçon).
- **Lecture.** Mesure prudente : une alerte quelconque sur le client suffit à le considérer comme vu.

---

## Bloc FIL — Filtrage des sanctions

### FIL-01 — Correspondances approchées avec la liste de sanctions

- **Question.** Des clients correspondent-ils à une entrée de la liste, malgré des variantes d'écriture ?
- **Logique.** Noms normalisés (majuscules, sans accents ni ponctuation, formes juridiques retirées, mots
  triés pour neutraliser l'ordre prénom / nom) ; similarité de séquences ≥ 0,88 ; qualification : forte
  (nom et date de naissance identiques, ou raison sociale), homonymie probable (date de naissance
  différente, à lever).
- **Référence.** Instruction n°001-03-2025, art. 6 ; recommandation 6 du GAFI.
- **Attention.** La liste du projet est **fictive**. Sur données réelles, utiliser les listes officielles
  (ONU, listes nationales) et traiter toute correspondance forte immédiatement.

---

## Bloc DEC / ALE — Déclarations et traitement des alertes

### DEC-01 — Déclarations des transactions en espèces (DTE)

- **Logique.** Cumul des opérations en espèces par client, par jour et par sens ≥ 15 M FCFA = DTE attendue ;
  rapprochement avec le registre ; exception = DTE absente. Annexe : taux de DTE manquantes par agence.
- **Hypothèse.** Les « opérations liées » sont approchées par le cumul journalier ; une définition plus
  large (plusieurs jours) relève d'OPE-01.

### ALE-01 — Alertes en souffrance

- **Logique.** Alertes ouvertes à la date d'arrêté depuis plus de 30 jours (délai interne, hypothèse) ;
  ventilation par ancienneté et par analyste.

### ALE-02 — Clôtures non justifiées ou en masse

- **Logique.** Alertes clôturées sans motif ; alertes clôturées par un même analyste le même jour au-delà
  de 15 clôtures (signal de clôture administrative sans analyse).

### ALE-03 — Délais des déclarations de soupçon

- **Logique.** Délai d'analyse (alerte → décision) > 30 jours et délai de transmission (décision → CENTIF)
  > 2 jours. La loi exige une déclaration « immédiate » (art. 60) : les deux délais sont des critères
  d'audit à aligner sur la procédure interne.

---

## Bloc KYC — Connaissance de la clientèle

| Test | Logique | Référence |
|---|---|---|
| **KYC-01** Complétude | Champs obligatoires vides (10 pour les personnes physiques, 7 pour les personnes morales) ; taux par agence | LU art. 16-17 ; Instr. 003-03-2025 art. 5 à 8 |
| **KYC-02** Pièces expirées | Pièce d'identité expirée à la date d'arrêté, avec le nombre d'opérations de la période | Instr. 003-03-2025 art. 6 |
| **KYC-03** Revues en retard | Dernière revue + périodicité (1, 2 ou 3 ans selon le risque, hypothèse) antérieure à la date d'arrêté | LU art. 19 |
| **KYC-04** PPE | Approbation de la haute direction absente ; classement autre que « élevé » ; réévaluation de plus de 3 ans | LU art. 29 |
| **KYC-05** Bénéficiaires effectifs | Personne morale sans bénéficiaire effectif identifié | Instr. 003-03-2025 art. 12 ; LU art. 25 |
| **KYC-06** Classification | PPE non classée « élevé » ; personne morale sans BE ou client exposé à un pays du GAFI classé « faible » | LU art. 6, 15, 29, 30 |

---

## Ajouter un test

1. Écrire une fonction `def xxx_07_mon_test(d: Donnees, p: Parametres) -> ResultatTest` dans le module du bloc.
2. L'ajouter à la liste `TESTS_...` du module et à l'ordre d'affichage dans `moteur.py`.
3. Ajouter ses paramètres dans `config/parametres.yaml` (avec la source ou la mention « hypothèse »).
4. Écrire un test unitaire dans `tests/test_regles.py` sur un petit jeu construit à la main.
