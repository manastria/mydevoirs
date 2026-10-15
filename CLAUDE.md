# MyDevoirs : notes de développement

Application de prise de devoirs en Python 3.11 / Kivy, empaquetée avec Briefcase 0.3.18 (`.msi` Windows, `.AppImage` Linux). Fork de `jgirardet/mydevoirs`, repris et maintenu sur `manastria/mydevoirs`. Le site de présentation est dans `site/`.

## Environnement

- Poetry, avec le venv dans `.venv` (`poetry.toml`). Il faut Python 3.11 :
  `poetry env use python3.11 && poetry install --with dev`.
- `.venv/`, `build/`, `dist/` et `logs/` sont ignorés par git.

## Lancer l'application

- `MYDEVOIRS_DEBUG=1 poetry run python -m mydevoirs` : données et réglages dans `/tmp/mydevoirs_debug`, sans toucher aux vraies données.
- Sans `MYDEVOIRS_DEBUG` : vraies données dans `~/.cache/MyDevoirs` et `~/.config/MyDevoirs`.
- Il faut la locale `fr_FR.utf8`. Sous WSL, WSLg suffit pour l'affichage. Sans `xclip`, Kivy affiche des avertissements sur le presse-papiers, sans conséquence.
- `make run` et `make build` sont cassés : ils appellent `main.py` et `scripted/build_executable.py`, qui n'existent pas.

## Tests

- `poetry run pytest -q`. Il faut un affichage réel (le fournisseur de fenêtre `mock` n'existe pas dans Kivy 2.3.1) : utiliser `xvfb-run -a` sur une machine sans écran.
- 3 échecs connus depuis la 1.3.0, sans rapport avec le code récent : `test_nice_date` (test périmé), `test_go_to_week_input` (freezegun incompatible avec Pony) et `test_set_locale_fr` (demande la locale `en_US.utf8`).
- Le job `test` de `.github/workflows/main.yml` est commenté : la CI ne lance aucun test.

## Repères dans le code

- **Réglages** : `mydevoirs/settings.py` (`AGENDA_PANEL`, `DEFAULT_SETTINGS`). Les types personnalisés sont enregistrés dans `MyDevoirsApp.build_settings`. `tests/test_settings.py` refuse tout type inconnu : ajouter une branche pour chaque nouveau type. Modifier un réglage de la section `agenda` appelle `go_agenda()`, qui reconstruit l'agenda.
- **Semaines A/B** : `mydevoirs/alternance.py`. La lettre se calcule à partir d'un lundi de référence, jamais à partir de la parité du numéro ISO.
- **Taille de la fenêtre** : `mydevoirs/fenetre.py`, appelé depuis `on_start` et `on_stop`, et non depuis `build`, que les tests appellent. Kivy ne donnant pas la taille de l'écran, on maximise la fenêtre pour mesurer la zone utile. Toujours utiliser `Window.system_size` : sous Windows, `Window.size` se lit en pixels physiques mais s'écrit en pixels logiques.
- **`mydevoirs.dist-info/` à la racine** : vestige (version 0.6.4, Briefcase 0.3.2). Quand on lance depuis la racine du dépôt, `importlib.metadata` le lit en priorité, et `VERSION` vaut alors 0.6.4. Les livrables n'ont pas ce problème. On ne peut pas simplement le supprimer : `settings.py` y lit la `Home-page`, absente de `pyproject.toml`.

## Construire l'AppImage en local

- `poetry run briefcase create linux appimage`, puis `build` et `package`. Briefcase construit dans Docker (image `ubuntu:18.04`). Sous WSL, il faut Docker Desktop avec l'intégration WSL. `--no-docker` construit sur l'hôte, avec un résultat moins portable.
- Garder `ca-certificates` dans `system_requires` (`[tool.briefcase.app.mydevoirs.linux]`) : sans lui, `appimagetool` ne peut pas télécharger son runtime dans l'image Docker.
- Pour tester l'AppImage : `APPIMAGE_EXTRACT_AND_RUN=1 ./dist/mydevoirs-X.Y.Z-x86_64.AppImage` (évite d'avoir besoin de FUSE).

## Documentation

- La documentation est dans `docs/`, en Markdown. Les images du README sont dans `docs/images/`.
- `docs/construire-msi.md` : construire et tester l'installateur Windows sur un PC.

## Publier une version

1. Sur `dev` :
   - changer la version aux deux endroits de `pyproject.toml` : `[tool.poetry] version = "X.Y.Z+manastria.1"` et `[tool.briefcase] version = "X.Y.Z"` ;
   - ajouter une section `## [X.Y.Z] - AAAA-MM-JJ` dans `CHANGELOG.md`, rédigée pour l'utilisateur.
2. Squash vers `master` :
   `git checkout master && git -c merge.ff=true merge --squash dev && git commit`.
   Le `-c merge.ff=true` est nécessaire si la config git globale contient `merge.ff = no`, qui fait échouer `--squash`.
3. Pousser :
   - `git push origin master` ;
   - puis `git tag -a vX.Y.Z -m "Publication de la version X.Y.Z" && git push origin vX.Y.Z`.

   Préférer un tag annoté, comme pour `v1.3.0` et `v1.3.1` : `run.py version` crée un tag léger.
4. Le tag déclenche `main.yml` : `build` (`.msi`), `build-linux` (`.AppImage`) puis `create-release`. La release est créée même si le job Linux échoue.
5. Vérifier avec `gh release view vX.Y.Z -R manastria/mydevoirs`, qui doit lister les deux fichiers.
6. Réaligner `dev` :
   `git tag archive/dev-avant-X.Y.Z dev && git branch -f dev master`.

Claude prépare tout en local. Le mainteneur pousse lui-même `master` et le tag.

## Git et GitHub

- `origin` = `manastria/mydevoirs`. Un clone fait avec `gh repo clone` ajoute aussi `upstream` = `jgirardet/mydevoirs`, projet d'origine qui n'est plus maintenu. Avec deux remotes, toujours passer `-R manastria/mydevoirs` à `gh`, ou lancer `gh repo set-default manastria/mydevoirs`.
- Le site est publié par `publier-site.yml` à chaque push sur `master` qui touche `site/`. `site/verifier.py` contrôle les fichiers liés.
- Messages de commit en français, préfixés : `feat:`, `fix:`, `ci:`, `chore:`.
