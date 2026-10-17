# Journal des modifications

Toutes les modifications notables de ce projet seront documentées dans ce fichier.
Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

---

## [1.3.2] - 2026-10-17

### Modifié (Changed)
- La fenêtre s'adapte à l'écran : elle s'ouvre maximisée au premier lancement, puis retrouve la taille qu'on lui a laissée en fermant MyDevoirs. Sur un petit écran (portable en 1366×768), le bas de l'agenda n'est plus caché.
- L'en-tête de l'agenda n'affiche plus qu'une semaine, celle qu'on regarde : son numéro, sa lettre, ses dates et sa position par rapport à aujourd'hui (« cette semaine », « dans 2 semaines »...). Un bouton « Aujourd'hui » y ramène quand on consulte une autre semaine.
- Le jour d'aujourd'hui est mis en couleur dans l'agenda. Les titres des jours n'indiquent plus la semaine ni l'année, déjà présentes dans l'en-tête.

- Les fichiers d'installation sont publiés sous des noms fixes (`MyDevoirs-Windows.msi`, `MyDevoirs-Linux.AppImage`), sans numéro de version. Le site propose ainsi un téléchargement direct de la dernière version, adapté à votre système.
- Le champ de saut de l'agenda accepte un numéro de semaine (`12`), une semaine d'une autre année (`3/2027`) ou une date (`JJ/MM/AAAA`, `AAAA-MM-JJ`).

### Corrigé (Fixed)
- Champ de saut de l'agenda : un numéro de semaine est cherché dans l'année de la semaine affichée, et non plus toujours dans l'année en cours. Une saisie incorrecte (semaine 53 inexistante, date impossible ou hors de 1900–2100) affiche un message en rouge et reste à l'écran pour être corrigée, au lieu d'être effacée. Les dates extrêmes (`01/01/0001`) ne risquent plus de faire planter le logiciel.
- Si MyDevoirs reste ouvert après minuit, le jour mis en couleur suit le changement de date.
- Quand la semaine commence un autre jour que le lundi, le numéro et la lettre de la semaine correspondent bien aux jours affichés.

---

## [1.3.1] - 2026-10-15

### Ajouté (Added)
- Semaines A/B réglables dans les paramètres (section « Semaines A/B ») : activer ou non l'alternance, choisir les libellés (« A, B », « 1, 2, 3 »...) et indiquer la lettre de la semaine en cours.
- Version Linux : un fichier `.AppImage` est publié avec chaque version, à côté de l'installateur Windows.

### Corrigé (Fixed)
- Les semaines A et B ne se décalent plus au changement d'année : le 4 janvier 2027 est bien une semaine B, après la semaine A du 28 décembre 2026.

---

## [1.3.0] - 2025-09-13

Ceci est la première version publiée après la reprise du projet par [manastria](https://github.com/manastria).

### Ajouté (Added)
- Gestion des numéros de semaine dans la vue agenda : « sem. N » à côté de chaque jour, et semaine affichée rappelée dans l'en-tête.
- Repérage des semaines A et B (semaines impaires / paires), pour les emplois du temps qui alternent.
- Badge « aujourd'hui » dans l'en-tête de l'agenda : date du jour et numéro de semaine.
- Champ de saisie pour naviguer rapidement vers une semaine ou un jour précis (numéro de semaine, `JJ/MM/AAAA` ou `AAAA-MM-JJ`).

### Corrigé (Fixed)
- Défaut d'affichage sur le premier jour du mois dans l'agenda.

---

## [1.2.1]

### Ajouté (Added)
- Ajout d'un thème "contrast".

---

## [1.1.0]

### Ajouté (Added)
- Il est désormais possible de choisir le premier jour de la semaine.

---

## [1.0.0]

### Ajouté (Added)
- Ajout de la fonctionnalité de suppression de matière.

---

## [0.7.0]

### Ajouté (Added)
- Ajout du lien vers l'aide.
- Ajout de la personnalisation des couleurs et des matières.
- Pour les développeurs : ajout d'un mode debug et test.

---
[1.3.0]: https://github.com/manastria/mydevoirs/releases/tag/v1.3.0
[1.2.1]: https://github.com/jgirardet/mydevoirs/releases/tag/v1.2.1
[1.1.0]: https://github.com/jgirardet/mydevoirs/releases/tag/v1.1.0
[1.0.0]: https://github.com/jgirardet/mydevoirs/releases/tag/v1.0.0
[0.7.0]: https://github.com/jgirardet/mydevoirs/releases/tag/v0.7.0