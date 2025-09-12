# Obtenir un installateur Windows

Pour générer un installateur Windows pour MyDevoirs :

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
