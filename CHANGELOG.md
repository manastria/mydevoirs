# Journal des modifications

Toutes les modifications notables de ce projet seront documentées dans ce fichier.
Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

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