# Construire le `.msi` sous Windows

Cette procédure produit l'installateur Windows sur un PC, pour tester une version avant de la publier. Elle reprend les étapes du job `build` de `.github/workflows/main.yml`, qui fait référence en cas de doute.

Briefcase ne construit pas de `.msi` depuis Linux ni WSL : il faut le faire sous Windows.

## Prérequis

- **Git for Windows**.
- **Python 3.11**, installé depuis python.org avec le lanceur `py`. L'application est construite avec la version de Python qui lance Briefcase.
- **Une connexion Internet** au premier passage : Briefcase télécharge son support Python et WiX.

Inutile d'installer WiX. Quand la variable d'environnement `WIX` n'existe pas, Briefcase 0.3.18 télécharge lui-même WiX 3.14 dans son dossier de données. La CI, elle, l'installe avec `choco` et définit `WIX`.

Si le téléchargement automatique échoue (réseau restreint, proxy), installer WiX Toolset v3.x (3.11 ou 3.14.x, **pas** v4, non supporté par Briefcase 0.3.x) depuis https://github.com/wixtoolset/wix3/releases, puis définir `WIX` vers son dossier d'installation :

```powershell
[System.Environment]::SetEnvironmentVariable('WIX', 'C:\Program Files (x86)\WiX Toolset v3.14', 'User')
```

Ouvrir un nouveau terminal puis vérifier : `Test-Path "$env:WIX\bin\candle.exe"` doit retourner `True`.

Côté Kivy, `[tool.briefcase.app.mydevoirs.windows]` dans `pyproject.toml` doit garder `kivy_deps.sdl2`, `kivy_deps.glew` et `kivy_deps.angle` (DLLs SDL2/GLEW/ANGLE) ainsi que `pywin32` (module `win32file` pour le filechooser). Sans eux : `Unable to find any valuable Window provider / _window_sdl2` à l'exécution (voir Dépannage).

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

## Dépannage

- **`Unable to find any valuable Window provider / _window_sdl2`** : DLL SDL2/ANGLE/GLEW manquantes dans le bundle. Vérifier la section `requires` de `pyproject.toml` (voir Prérequis), puis :
  ```powershell
  poetry run briefcase update windows --requirements
  poetry run briefcase build windows
  ```
- **Signature** : `--no-sign` n'est pas un argument valide sur Briefcase 0.3.18. Omettre simplement les options de signature (ou utiliser `--adhoc-sign`, voir étape 3).
- **`No module named stub`** (le log affiche `Running app module: stub` au lieu de `mydevoirs`) : `briefcase run windows` ne relance `build` que si le binaire n'existe pas encore. Si `mydevoirs.exe` existe déjà mais n'a jamais été retouché par `rcedit` (installation fraîche de l'outil, cache Briefcase nettoyé, `create` lancé sans `build` ensuite), il garde le nom de module par défaut du binaire *stub* et ne démarre pas. Il suffit de lancer `build` explicitement avant `run` :
  ```powershell
  poetry run briefcase build windows
  poetry run briefcase run windows
  ```
