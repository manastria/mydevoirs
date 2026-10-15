# Construire le `.msi` sous Windows

Cette procédure produit l'installateur Windows sur un PC, pour tester une version avant de la publier. Elle reprend les étapes du job `build` de `.github/workflows/main.yml`, qui fait référence en cas de doute.

Briefcase ne construit pas de `.msi` depuis Linux ni WSL : il faut le faire sous Windows.

## Prérequis

- **Git for Windows**.
- **Python 3.11**, installé depuis python.org avec le lanceur `py`. L'application est construite avec la version de Python qui lance Briefcase.
- **Une connexion Internet** au premier passage : Briefcase télécharge son support Python et WiX.

Inutile d'installer WiX. Quand la variable d'environnement `WIX` n'existe pas, Briefcase 0.3.18 télécharge lui-même WiX 3.14 dans son dossier de données. La CI, elle, l'installe avec `choco` et définit `WIX`.

## 1. Récupérer les sources sur le disque Windows

Ne pas construire depuis `\\wsl.localhost\...` : les environnements virtuels et WiX supportent mal les chemins réseau.

Pousser d'abord la branche à tester (`git push origin dev` : un push sur `dev` ne déclenche aucune construction), puis :

```powershell
git clone -b dev https://github.com/manastria/mydevoirs.git C:\dev\mydevoirs
cd C:\dev\mydevoirs
```

Pour une mise à jour : `git pull` dans ce dossier.

## 2. Installer Poetry et les dépendances

À faire une seule fois :

```powershell
py install 3.11
py -3.11 -m pip install --user pipx
py -3.11 -m pipx ensurepath
py -3.11 -m pipx install poetry
```

Fermer puis rouvrir le terminal pour que `poetry` soit dans le `PATH`. Ensuite, dans `C:\dev\mydevoirs` :

```powershell
poetry env use (py -3.11 -c "import sys; print(sys.executable)")
poetry install --with dev
```

## 3. Construire

```powershell
poetry run briefcase create windows
poetry run briefcase build windows
poetry run briefcase package windows --adhoc-sign
```

`--adhoc-sign` produit un `.msi` non signé, sans poser de question sur un certificat. Windows SmartScreen signalera un « éditeur inconnu » : c'est normal pour un test.

Le fichier est créé dans `dist\mydevoirs-X.Y.Z.msi`, où `X.Y.Z` est la `version` de `[tool.briefcase]` dans `pyproject.toml`.

Après une modification du code, `create` n'est plus nécessaire :

```powershell
poetry run briefcase build windows -u
poetry run briefcase package windows --adhoc-sign
```

## Avant d'installer le `.msi` de test

- **Numéro de version.** Si le `.msi` porte le même numéro que la version déjà installée, désinstaller celle-ci d'abord. Autre solution : changer temporairement les deux champs `version` de `pyproject.toml` (`1.3.1` devient `1.3.2`, par exemple), sans commiter.
- **Données.** La version installée utilise les vraies données de l'utilisateur Windows (base et `settings.ini` dans son profil). Faire une sauvegarde avant de tester sur un PC qui sert vraiment, et vérifier dans le `CHANGELOG.md` ce que la nouvelle version modifie.

## Tester sans `.msi`

Pour essayer une modification du code sous Windows, le `.msi` n'est pas nécessaire. Après l'étape 2 :

- `poetry run python -m mydevoirs` lance l'application depuis les sources. Pour utiliser des données temporaires, lancer d'abord `$env:MYDEVOIRS_DEBUG=1` : le réglage vaut jusqu'à la fermeture du terminal.
- `poetry run briefcase run windows` lance l'application construite par `build`, sans l'installer.

Le `.msi` ne sert qu'à tester l'installation elle-même : raccourcis, désinstallation, mise à jour par-dessus une version précédente.
