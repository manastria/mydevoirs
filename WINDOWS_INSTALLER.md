# Obtenir un installateur Windows

Pour générer un installateur Windows pour MyDevoirs :

## Prérequis (Windows / Briefcase)

Briefcase 0.3.x utilise le WiX Toolset (v3.x) pour produire l'installateur MSI. WiX n'est pas un paquet pip ; c'est un outil natif Windows à installer séparément.

1. Installer le « WiX Toolset v3.x » (3.11 ou 3.14.x) depuis le site officiel.
2. Définir la variable d'environnement `WIX` vers le dossier d'installation de WiX (exemple par défaut) : `C:\Program Files (x86)\WiX Toolset v3.11`

   PowerShell (choisir User ou Machine) :
   ```powershell
   # Pour l'utilisateur courant
   [System.Environment]::SetEnvironmentVariable('WIX','C:\\Program Files (x86)\\WiX Toolset v3.11','User')

   # Pour toute la machine (peut nécessiter un PowerShell admin)
   [System.Environment]::SetEnvironmentVariable('WIX','C:\\Program Files (x86)\\WiX Toolset v3.11','Machine')
   ```

3. Ouvrir un nouveau terminal puis vérifier :
   ```powershell
   echo $env:WIX
   Test-Path "$env:WIX\bin\candle.exe"   # doit retourner True
   ```

Notes :
- Ne pas installer WiX v4 avec Briefcase 0.3.2 : non supporté.
- Si vous voyez « The WIX environment variable does not point to an install of the WiX Toolset. Current value: WindowsPath('.') », la variable `WIX` est incorrecte — corrigez-la puis rouvrez le terminal.

## Étapes de construction

1. Installer les dépendances :
   ```bash
   poetry install
   ```
2. Créer l'application pour Windows :
   ```bash
   poetry run briefcase create windows
   ```
3. Construire l'exécutable :
   ```bash
   poetry run briefcase build windows
   ```
4. Générer l'installateur :
   ```bash
   poetry run briefcase package windows
   ```

L'installateur `.msi` sera disponible dans le dossier `dist`.

