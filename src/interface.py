from pathlib import Path
from .models import Livre, LivreNumerique, Bibliotheque
from typing import Optional

def create_demo_library() -> Bibliotheque:
    b = Bibliotheque("Demo Bibliotheque")
    b.ajouter_livre(Livre("1984", "George Orwell", "ISBN123"))
    b.ajouter_livre(Livre("Les Miserables", "Victor Hugo", "ISBN456"))
    b.ajouter_livre(Livre("Le Petit Prince", "Antoine de Saint-Exupery", "ISBN789"))
    b.ajouter_livre(LivreNumerique("Digital Fortress", "Dan Brown", "ISBN101", "2MB"))
    return b

def save_library(bibliotheque: Bibliotheque, path: str) -> None:
    bibliotheque.sauvegarder(path)

def load_library(path: str) -> Bibliotheque:
    b = Bibliotheque(Path(path).stem)
    b.charger(path)
    return b

def export_library_csv(bibliotheque: Bibliotheque, path: str) -> None:
    bibliotheque.export_csv(path)

def main_demo() -> None:
    # Keep main_demo as a simple entry that runs the TP1-style demo
    run_tp1_demo()


def run_tp1_demo() -> None:
    """Run the TP1 demo flow inside the interface module.

    - create sample books
    - perform search and deletion
    - save JSON and export CSV into project-level `data/` directory
    - reload from saved JSON
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    ma_bibliotheque = Bibliotheque("La Bible aux Tcheques")
    # sample books
    livre1 = Livre("1984", "George Orwell", "ISBN123")
    livre2 = Livre("Les Miserables", "Victor Hugo", "ISBN456")
    livre3 = Livre("Le Petit Prince", "Antoine de Saint-Exupery", "ISBN789")
    livre4 = LivreNumerique("Digital Fortress", "Dan Brown", "ISBN101", "2MB")

    # add books
    ma_bibliotheque.ajouter_livre(livre1)
    ma_bibliotheque.ajouter_livre(livre2)
    ma_bibliotheque.ajouter_livre(livre3)
    ma_bibliotheque.ajouter_livre(livre4)

    # search by title
    resultats = ma_bibliotheque.recherche_par_titre("1984")
    for livre in resultats:
        print(f"Trouve : {livre.titre} par {livre.auteur}")

    # suppression
    if ma_bibliotheque.supprimer_livre("ISBN456"):
        print("Suppression reussie pour ISBN456")
    else:
        print("Livre a supprimer non trouve")

    # recherche par auteur
    resultats = ma_bibliotheque.recherche_par_auteur("Victor Hugo")
    for livre in resultats:
        print(f"Trouve : {livre.titre} par {livre.auteur}")

    # persistence
    bib_path = data_dir / "bib.json"
    csv_path = data_dir / "catalogue.csv"
    try:
        ma_bibliotheque.sauvegarder(str(bib_path))
        print(f"Sauvegarde dans '{bib_path}' reussie")
    except Exception as e:
        print(f"Erreur sauvegarde: {e}")

    try:
        ma_bibliotheque.export_csv(str(csv_path))
        print(f"Export CSV vers '{csv_path}' reussi")
    except Exception as e:
        print(f"Erreur export CSV: {e}")

    try:
        ma_bibliotheque.charger(str(bib_path))
        print(f"Chargement depuis '{bib_path}' reussi")
    except Exception as e:
        print(f"Erreur chargement: {e}")

if __name__ == "__main__":
    main_demo()
