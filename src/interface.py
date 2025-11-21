from pathlib import Path
import sys
try:
    from .models import AggregatedLivre as Livre, LivreNumerique
    from .file_manager import BibliothequeAvecFichier
except Exception:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.models import AggregatedLivre as Livre, LivreNumerique
    from src.file_manager import BibliothequeAvecFichier
from typing import Optional
from .file_manager import BibliothequeAvecFichier
from .file_manager import BibliothequeAvecFichier as _BM

def create_demo_library() -> BibliothequeAvecFichier:
    b = BibliothequeAvecFichier("Demo Bibliotheque")
    b.ajouter_livre(Livre("Seigneur des anneux", "John Tolkien", "9788845292613"))
    b.ajouter_livre(Livre("Harry Potter", "J.K. Rowling", "9780747532743"))
    b.ajouter_livre(Livre("Les Rois maudits", "Maurice Druon", "9782253005553"))
    b.ajouter_livre(LivreNumerique("King in yellow", "Stephen King", "9781501142970", "2MB"))
    return b

def save_library(bibliotheque: BibliothequeAvecFichier, path: str) -> None:
    bibliotheque.sauvegarder(path)

def load_library(path: str) -> BibliothequeAvecFichier:
    b = BibliothequeAvecFichier(Path(path).stem)
    b.charger(path)
    return b

def export_library_csv(bibliotheque: BibliothequeAvecFichier, path: str) -> None:
    bibliotheque.export_csv(path)

def main_demo() -> None:
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

    ma_bibliotheque = BibliothequeAvecFichier("Le tiroire")

    livre1 = Livre("Seigneur des anneux", "John Tolkien", "9788845292613")
    livre2 = Livre("Harry Potter ", "J.K. Rowling ", "9780747532743 ")
    livre3 = Livre("Les Rois maudits ", "Maurice Druon ", "9782253005553 ")
    livre4 = Livre("King in yellow ", "Stephen King ", "9781501142970 ")

    ma_bibliotheque.ajouter_livre(livre1)
    ma_bibliotheque.ajouter_livre(livre2)
    ma_bibliotheque.ajouter_livre(livre3)
    ma_bibliotheque.ajouter_livre(livre4)

    ma_bibliotheque.afficher()

    resultats = ma_bibliotheque.recherche_par_titre("King in yellow ")
    for livre in resultats:
        print(f"Trouve : {livre.titre} par {livre.auteur}")

    if ma_bibliotheque.supprimer_livre("9788845292613"):
        print("Suppression effectuee")
    else:
        print("Livre a supprimer non trouve")

    resultats = ma_bibliotheque.recherche_par_auteur("John Tolkien")
    for livre in resultats:
        print(f"Trouve : {livre.titre} par {livre.auteur}")
    

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
    else:
        ma_bibliotheque.afficher()


def create_demo_users():
    from .users import User
    u1 = User.create("alice", "password123", subscription_type="basique")
    u2 = User.create("bob", "securepwd", subscription_type="premium")
    u2.is_admin = True
    return [u1, u2]


def save_users(users, path: str) -> None:
    BibliothequeAvecFichier.sauvegarder_users(users, path)


def load_users(path: str):
    return BibliothequeAvecFichier.charger_users(path)

if __name__ == "__main__":
    main_demo()
