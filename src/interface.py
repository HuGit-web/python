from pathlib import Path
import sys
try:
    # when used as a package (recommended)
    from .models import Livre, LivreNumerique, Bibliotheque
except Exception:
    # when executed directly (python src/interface.py) fall back to absolute import
    # ensure project root is on sys.path so `import src` works
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.models import Livre, LivreNumerique, Bibliotheque
from typing import Optional

def create_demo_library() -> Bibliotheque:
    b = Bibliotheque("Demo Bibliotheque")
    b.ajouter_livre(Livre("Seigneur des anneux", "John Tolkien", "9788845292613"))
    b.ajouter_livre(Livre("Harry Potter", "J.K. Rowling", "9780747532743"))
    b.ajouter_livre(Livre("Les Rois maudits", "Maurice Druon", "9782253005553"))
    b.ajouter_livre(Livre("King in yellow", "Stephen King", "9781501142970"))
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

    ma_bibliotheque = Bibliotheque("Le tiroire")
    # sample books
    livre1 = Livre("Seigneur des anneux", "John Tolkien", "9788845292613")
    livre2 = Livre("Harry Potter", "J.K. Rowling", "9780747532743")
    livre3 = Livre("Les Rois maudits", "Maurice Druon", "9782253005553")
    livre4 = Livre("King in yellow", "Stephen King", "9781501142970")

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
    if ma_bibliotheque.supprimer_livre("9788845292613"):
        print("Suppression reussie pour 9788845292613")
    else:
        print("Livre a supprimer non trouve")

    # recherche par auteur
    resultats = ma_bibliotheque.recherche_par_auteur("John Tolkien")
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
