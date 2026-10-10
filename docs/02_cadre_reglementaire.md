# 2. Cadre réglementaire et normatif

> Synthèse établie en octobre 2026 à partir des textes publiés par la BCEAO, la Commission Bancaire de
> l'UMOA et le GAFI. Elle ne remplace pas la lecture des textes officiels : vérifier la version en
> vigueur et les **dispositions nationales plus contraignantes** (chaque État transpose la loi uniforme).
> Les éléments non confirmés sont signalés **[à vérifier]**.

## 2.1 Les textes de référence

| Texte | Objet | Utilisation dans le projet |
|---|---|---|
| **Loi uniforme relative à la LBC/FT/FP** dans les États membres de l'UMOA (adoptée par le Conseil des Ministres le 31 mars 2023, transposée par chaque État) | Obligations de vigilance, déclarations, contrôle interne, sanctions | Critères de la plupart des tests |
| **Décision n°021 du 21/12/2023/CM/UMOA** | Montants seuils pour la mise en œuvre de la loi uniforme | Seuils de 9, 10, 15 et 50 M FCFA |
| **Décision n°003 du 28/03/2024/CM/UMOA** | Seuils complémentaires (bureaux de change, métaux précieux, immobilier) | Contexte |
| **Instruction BCEAO n°001-03-2025** du 18 mars 2025 | Organisation, contrôle interne et conformité LBC/FT des institutions financières | Surveillance, filtrage, audit annuel |
| **Instruction BCEAO n°002-03-2025** du 18 mars 2025 | Seuil de déclaration du transport physique intracommunautaire d'espèces | Contexte (seuil [à vérifier]) |
| **Instruction BCEAO n°003-03-2025** du 18 mars 2025 | Identification, vérification de l'identité et connaissance de la clientèle | Tests KYC |
| **Instruction BCEAO n°233/07/2024** du 16 juillet 2024 | Paiement d'une dette en espèces : plafond de 5 M FCFA | Paramètre de référence |
| **Instruction BCEAO n°231/07/2024** du 16 juillet 2024 | Déclaration du transport physique international d'espèces : 5 M FCFA | Contexte |
| **Circulaires de la Commission Bancaire de 2017** : n°03-2017/CB/C (contrôle interne), n°04-2017/CB/C (gestion des risques), n°05-2017/CB/C (conformité) | Cadre général du contrôle interne bancaire | Méthodologie |
| **Recommandations du GAFI** et déclarations publiques (listes « noire » et « grise ») | Standards internationaux, pays à risque | Test OPE-05 |

Les textes de l'UMOA sont rassemblés sur la page LBC/FT de la Commission Bancaire :
<https://cb-umoa.org/en/lbc-ft>. La loi uniforme est publiée sur le site de la BCEAO :
<https://bceao.int/sites/default/files/2025-02/Loi-uniforme-LBCFTFP-Mars-2023-vf.pdf>.

## 2.2 Les articles mobilisés (loi uniforme LBC/FT/FP de 2023)

| Article | Contenu (résumé) | Tests |
|---|---|---|
| Art. 6 et 15 | Approche fondée sur les risques ; évaluation des risques par l'assujetti (y compris nouveaux produits et technologies) | KYC-06 |
| Art. 12 et 13 | Politiques, procédures et contrôle interne ; contrôles périodiques et permanents ; analyse des opérations atypiques | Méthodologie |
| Art. 16 et 17 | Conditions préalables à l'entrée en relation ; cas d'identification (dont opérations multiples en espèces sur une journée, point i) | KYC-01 |
| Art. 19 | Vigilance constante sur la relation d'affaires (mise à jour des informations et du profil) | KYC-03, OPE-03 |
| Art. 20 | Vigilance constante sur les opérations ; interdiction des comptes anonymes | OPE-01 à OPE-06 |
| Art. 21 | Surveillance particulière : espèces au-delà d'un seuil, opérations complexes ou inhabituelles au regard du profil ; **rapport écrit confidentiel** | OPE-01, OPE-03, ALE-02 |
| Art. 23 | Conservation des documents : **10 ans** | ALE-02 |
| Art. 25 | Conduite à tenir lorsque les obligations de vigilance ne peuvent être satisfaites | KYC-05 |
| Art. 29 | **PPE** : autorisation de la haute direction, origine du patrimoine et des fonds, surveillance renforcée, réévaluation du profil **tous les trois ans** (al. 3) | KYC-04 |
| Art. 30 | Pays présentant un risque plus élevé | OPE-05 |
| Art. 31 et 32 | Correspondance bancaire transfrontalière ; interdiction des banques fictives | Hors périmètre |
| Art. 39 à 45 | Virements électroniques : informations sur le donneur d'ordre et le bénéficiaire | Hors périmètre (piste d'extension) |
| Art. 60 et 61 | **Déclaration de soupçon** à la CENTIF « immédiatement » ; abstention avant exécution ou information sans délai | ALE-03 |
| Art. 63 | Interdiction de divulgation (« tipping off ») | Garde-fou du projet |
| Art. 72 | Déclaration des transactions en espèces à la CENTIF (seuil fixé par la Décision n°021) | DEC-01 |

## 2.3 Les seuils chiffrés

| Seuil | Objet | Source | Paramètre |
|---|---|---|---|
| **15 000 000 FCFA** | Déclaration à la CENTIF des transactions en espèces, opération unique ou opérations liées | Décision n°021/2023, art. 72 LU | `declaration_especes_centif` |
| **9 000 000 FCFA** | Identification lors d'opérations multiples en espèces sur une journée ou à fréquence inhabituelle | Décision n°021/2023, art. 17 i) LU | `especes_multiples_journalieres` |
| **10 000 000 FCFA** | Examen particulier des opérations d'une complexité inhabituelle ou injustifiée | Décision n°021/2023, art. 21 LU | `examen_particulier_complexe` |
| **50 000 000 FCFA** | Examen particulier des paiements en espèces ou au porteur | Décision n°021/2023, art. 21 LU | `examen_particulier_especes` |
| **5 000 000 FCFA** | Plafond de paiement d'une dette en espèces (sauf entre particuliers hors besoins professionnels) | Instruction n°233/07/2024 | `paiement_dette_especes` |
| **5 000 000 FCFA** | Déclaration en douane du transport physique d'espèces vers ou depuis un État tiers | Instruction n°231/07/2024 | — |
| 10 000 000 FCFA **[à vérifier]** | Déclaration du transport physique intracommunautaire d'espèces (chiffre relayé par la presse) | Instruction n°002-03-2025 | — |
| **25 %** | Détention du capital ou des droits de vote caractérisant le bénéficiaire effectif | Instruction n°003-03-2025, art. 2 | KYC-05 |
| **3 ans** | Réévaluation du profil des PPE | Loi uniforme, art. 29 al. 3 | `reevaluation_ppe_annees` |
| **10 ans** | Conservation des documents | Loi uniforme, art. 23 | — |

Remarques :

- Le seuil de 15 M FCFA figurait déjà dans l'Instruction n°010-09-2017 prise sous l'ancienne loi uniforme ; il
  est désormais fixé par la Décision n°021/2023.
- Les montants de la Décision n°021 sont repris de la synthèse publiée par *Droit Médias Finance*, qui cite
  le texte en toutes lettres : les confronter au texte officiel avant tout usage sur données réelles.
- Le **délai** de transmission des déclarations de transactions en espèces n'est pas testé **[à vérifier
  dans le texte national]**.

## 2.4 Les instructions BCEAO du 18 mars 2025 : ce qu'elles changent pour l'audit interne

**Instruction n°001-03-2025 (contrôle interne et conformité LBC/FT).**

- Le système d'information doit permettre le **profilage des clients**, le **filtrage en temps réel**, le
  **suivi des mouvements avec génération d'alertes** et l'identification des opérations suspectes ; il est
  **révisé au moins une fois par an** (art. 6). Les mesures de sanctions ciblées sont prises en compte
  « sans délai », défini comme 24 heures au plus (art. 2).
- Le dispositif de contrôle LBC/FT est **audité au moins une fois par an**, les conclusions étant
  soumises à l'organe délibérant et reprises dans le rapport annuel (art. 11 et 12).
- Un rapport annuel LBC/FT est transmis dans les **deux mois** suivant la clôture de l'exercice (art. 12).
- La formation du personnel suit un programme annuel documenté (art. 9 et 10).

**Instruction n°003-03-2025 (KYC).** Identification et vérification des personnes physiques (art. 5 et 6,
sur l'original d'une pièce officielle en cours de validité avec photographie), des personnes morales
(art. 7 et 8), des mandataires (art. 11) et des bénéficiaires effectifs (art. 12, avec consultation du
registre des bénéficiaires effectifs).

C'est l'article 11 de l'Instruction n°001-03-2025 qui fonde ce projet : **l'audit annuel du dispositif**
gagne à être outillé pour couvrir 100 % des opérations plutôt qu'un échantillon.

## 2.5 Les listes du GAFI (au 19 juin 2026)

Plénière des 17 au 19 juin 2026 ; prochaine plénière annoncée du 26 au 30 octobre 2026.

- **Juridictions faisant l'objet d'un appel à action** : Corée du Nord, Iran, Myanmar.
- **Juridictions sous surveillance renforcée (22)** : Angola, Bolivie, Bosnie-Herzégovine, Bulgarie,
  Cameroun, Côte d'Ivoire, RD Congo, Haïti, Irak, Kenya, Koweït, Laos, Liban, Monaco, Népal,
  Papouasie-Nouvelle-Guinée, Soudan du Sud, Syrie, Venezuela, Viêt Nam, Îles Vierges britanniques, Yémen.
- **Mouvements récents** : ajout de la Bosnie-Herzégovine et de l'Irak, retrait de l'Algérie et de la
  Namibie (juin 2026) ; retrait de l'Afrique du Sud, du Burkina Faso, du Mozambique et du Nigeria
  (octobre 2025).
- Dans l'UEMOA, la **Côte d'Ivoire** reste sous surveillance renforcée (engagement d'octobre 2024) ; en juin
  2026, le GAFI a jugé son plan d'action substantiellement achevé et justifiant une visite sur place.

Ces listes changent trois fois par an : le paramètre `listes_gafi` doit être mis à jour après chaque
plénière (source : <https://www.fatf-gafi.org>).

## 2.6 Normes professionnelles de l'audit interne

- **Normes mondiales d'audit interne de l'IIA** (en vigueur depuis le 9 janvier 2025) : planification fondée
  sur les risques, preuves suffisantes et documentées, communication des constats et suivi.
- **Modèle des trois lignes** : la conformité (2e ligne) pilote le dispositif LBC/FT ; l'audit interne
  (3e ligne) en évalue l'efficacité de façon indépendante. **L'audit ne déclare pas à la CENTIF.**
- **COSO 2013** pour l'évaluation du contrôle interne (environnement de contrôle, évaluation des risques,
  activités de contrôle, information et communication, pilotage).

## 2.7 Contexte de supervision

D'après le résumé du rapport annuel 2025 de la Commission Bancaire de l'UMOA, le système bancaire comptait
161 établissements de crédit pour un total de bilan de 82 298,8 milliards de FCFA ; la Commission a créé le
31 juillet 2025 un **Pôle de conformité LBC/FT** au sein de son Secrétariat général
([résumé du rapport annuel 2025](https://www.cb-umoa.org/sites/default/files/RESUME%20DU%20RAPPORT%20ANNUEL%202025%20DE%20LA%20COMMISSION%20BANCAIRE.pdf)).
