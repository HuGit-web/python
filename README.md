Projet : Application de gestion de bibliothèque

J'ai travailler en colaboration avec Ysmahel Costedoat-Descouzeres

Petit projet Python (CLI + GUI Tkinter) pour gérer une bibliothèque : livres, exemplaires,
utilisateurs, prêts, réservations et persistances simples en JSON.

**Structure importante**
- `src/` : code source (modèles, gestion fichiers, GUI)
- `data/` : fichiers persistants (`bib.json`, `users.json`)
- `tests/` : tests pytest
- `main.py` : point d'entrée (choix CLI / GUI)

## Prérequis
- Python 3.10+ (un environnement virtuel est recommandé)
- Dépendances listées dans `requirements.txt` (installables avec pip)

## Démarrer (PowerShell)

```powershell
# Créer/activer l'environnement virtuel (si nécessaire)
python -m venv .venv
& .\.venv\Scripts\Activate.ps1

# Installer dépendances
pip install -r requirements.txt

# Lancer l'application (menu CLI ou GUI)
python main.py
```

## Utilisateurs & accès
- Les comptes sont dans `data/users.json` (non versionné par défaut).
- Un compte admin existe (par ex. `bob`). Par sécurité, changez les mots de passe avant
  d'exposer le dépôt.

## Persistance
- Données sauvegardées : `data/bib.json` (catalogue) et `data/users.json` (utilisateurs).
- Sauvegarde atomique/transactionnelle implémentée pour éviter les pertes partielles.

## Tests

```powershell
# Activer venv, puis
pytest -q
```

## Notes
- `data/` est ignoré par `.gitignore` pour éviter de pousser des données runtime.
- Pour toute modification structurelle, vérifier `src/file_manager.py` (I/O) et `src/users.py`.

