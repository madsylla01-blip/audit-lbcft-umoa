# 8. Évaluation des tests (« tester les tests »)

> Page générée par `python -m lbcft_audit rapport`. Elle n'a de sens que sur des données synthétiques :
> sur des données réelles, la « vérité terrain » n'existe pas et la qualité des tests s'apprécie par la
> revue sur pièces d'un échantillon d'exceptions.

Le générateur de données injecte des schémas connus (fractionnement, comptes de passage, réseaux, etc.) et
des **situations atypiques mais légitimes**. On peut donc mesurer, pour chaque scénario de l'audit :

- le **rappel** : part des cas injectés effectivement détectés (un test qui rate des cas est dangereux) ;
- la **précision** : part des clients signalés relevant d'un schéma suspect injecté (un test trop bavard
  épuise les équipes et noie les vrais cas).

| Test | Typologie ciblée | Cas injectés | Cas détectés | Rappel | Clients signalés | dont schémas suspects | dont situations légitimes | Précision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPE-01 | FRACTIONNEMENT | 10 | 10 | 100 % | 11 | 10 | 1 | 91 % |
| OPE-02 | COMPTE_DE_PASSAGE | 8 | 8 | 100 % | 8 | 8 | 0 | 100 % |
| OPE-03 | INCOHERENCE_PROFIL | 8 | 8 | 100 % | 34 | 31 | 3 | 91 % |
| OPE-04 | REACTIVATION_DORMANT | 6 | 6 | 100 % | 7 | 6 | 1 | 86 % |
| OPE-05 | PAYS_A_RISQUE | 5 | 5 | 100 % | 5 | 5 | 0 | 100 % |
| OPE-06 | RESEAU | 10 | 10 | 100 % | 13 | 10 | 3 | 77 % |
| FIL-01 | SANCTIONS_CORRESPONDANCE | 3 | 3 | 100 % | 3 | 3 | 0 | 100 % |

## Faux positifs : pourquoi la revue sur pièces reste indispensable

Les situations légitimes signalées par les tests, et l'explication qui permet de les lever :

| Test | Client | Explication (justificatif) |
|---|---|---|
| OPE-01 | CL00083 | Recettes de fin d'année cohérentes avec le chiffre d'affaires |
| OPE-03 | CL00122 | Indemnisation d'un sinistre : justificatif disponible |
| OPE-03 | CL00321 | Indemnité de départ à la retraite : justificatif disponible |
| OPE-03 | CL00513 | Produit de cession d'un terrain (acte notarié) : justificatif disponible |
| OPE-04 | CL00818 | Réactivation par un rappel de pension documenté |
| OPE-06 | CL00121 | Membres d'un même foyer (justificatif de domicile) |
| OPE-06 | CL01016 | Membres d'un même foyer (justificatif de domicile) |
| OPE-06 | CL01081 | Membres d'un même foyer (justificatif de domicile) |

## Lecture

- Un rappel de 100 % sur un jeu synthétique ne garantit rien sur des données réelles : les typologies
  injectées sont celles que les tests cherchent. L'intérêt est ailleurs : vérifier que le code fait ce que
  la méthodologie annonce, et **calibrer les paramètres** en observant l'arbitrage rappel / précision.
- Les tests unitaires (`tests/`) vérifient ces résultats à chaque modification du code (intégration continue).
