# 1. Contexte et problématique

## 1.1 Le constat de départ

Dans les banques de l'UMOA, le dispositif de lutte contre le blanchiment de capitaux et le financement du
terrorisme (LBC/FT) repose sur trois piliers : bien connaître ses clients (KYC), surveiller leurs opérations
pour repérer l'inhabituel, et déclarer à la CENTIF ce qui reste suspect après analyse.

Le deuxième pilier est le plus difficile à évaluer. Un outil de surveillance produit des alertes ; un analyste
les traite ; quelques-unes deviennent des déclarations de soupçon. Mais **personne ne voit les opérations
qui n'ont déclenché aucune alerte**. Un dispositif peut sembler fonctionner (les alertes sont traitées, les
déclarations partent) tout en laissant passer des typologies entières, faute de scénario adapté.

C'est précisément le rôle de l'audit interne, troisième ligne de maîtrise, de porter un regard indépendant
sur cette question. L'Instruction BCEAO n°001-03-2025 lui en donne d'ailleurs l'occasion chaque année : le
dispositif de contrôle LBC/FT doit être audité **au moins une fois par an** (art. 11).

## 1.2 La problématique

> **Le dispositif de surveillance LBC/FT de la banque détecte-t-il réellement les opérations à risque, et
> les alertes sont-elles analysées et déclarées dans les délais ?**

Elle se décline en cinq questions d'audit :

1. **Détection** — Les typologies connues (fractionnement des espèces, comptes de passage, réseaux de
   prête-noms, réactivation de comptes dormants, flux avec des pays à risque) sont-elles couvertes ?
2. **Filtrage** — La clientèle est-elle correctement filtrée contre les listes de sanctions, malgré les
   variantes d'orthographe ?
3. **Traitement** — Les alertes sont-elles traitées dans les délais, et leurs clôtures justifiées ?
4. **Déclaration** — Les déclarations de soupçon et les déclarations de transactions en espèces sont-elles
   transmises, et à temps ?
5. **Connaissance client** — Les dossiers (pièces, profils, PPE, bénéficiaires effectifs, classification)
   permettent-ils une surveillance pertinente ?

## 1.3 Le parti pris : l'analyse exhaustive des données

L'approche traditionnelle teste un échantillon de dossiers et d'alertes. Elle dit si les alertes **traitées**
l'ont été correctement, mais pas ce que l'outil **n'a pas vu**. Ce projet montre comment un auditeur peut :

- **réexécuter de façon indépendante** des scénarios de détection sur 100 % des opérations ;
- **comparer** les clients qu'il identifie à ceux qui ont reçu une alerte de la banque (mesure de couverture) ;
- **tester exhaustivement** les données KYC, les registres de déclarations et la file des alertes ;
- produire des **feuilles de travail** et des **constats au format 5C** reproductibles.

## 1.4 Pourquoi des données fictives

Les données bancaires sont couvertes par le secret professionnel et par la protection des données
personnelles : elles ne peuvent pas être publiées. Le projet s'appuie donc sur une banque imaginaire, la
**Banque Fictive de l'Union (BFU)**, dont les données sont générées par programme :

- 1 200 clients, 1 386 comptes, près de 98 000 opérations sur 12 mois ;
- les alertes produites par un outil de surveillance simulé (4 scénarios, dont une liste de pays à risque
  restée figée en 2024) ;
- les registres de déclarations de soupçon et de déclarations de transactions en espèces ;
- une liste de sanctions **fictive**.

Des typologies de blanchiment et des défaillances de processus y sont injectées volontairement, ainsi que
des situations atypiques mais légitimes (faux positifs à lever). Comme on connaît la « vérité terrain », on
peut mesurer la performance des tests eux-mêmes (voir `08_evaluation_des_tests.md`).

## 1.5 Ce que le projet n'est pas

- Ce n'est pas un outil de surveillance LBC/FT en production : c'est un outil d'**audit** de ce dispositif.
- Il ne qualifie pas de soupçon : les exceptions sont **vérifiées sur pièces**, puis transmises à la
  conformité, seule habilitée à déclarer à la CENTIF.
- Ses paramètres (seuils, listes, délais) sont un point de départ à adapter au texte national, à la
  politique de la banque et au jugement de l'auditeur.
