from pathlib import Path
from src.interface import (
    create_demo_library,
    save_library,
    load_library,
    export_library_csv
)

from src.interface import (
    create_demo_library,
    save_library,
    load_library,
    export_library_csv
)

from src.gui import run_gui

def _choose_mode():
    print("Choose mode:\n1) Demo CLI\n2) GUI")
    choice = input("Mode (1 or 2): ").strip()
    return choice

def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    bib_json = data_dir / "bibliotheque.json"
    bib_csv = data_dir / "bibliotheque.csv"

    bibliotheque = create_demo_library()
    print("Bibliotheque de demonstration creee :")
    bibliotheque.afficher()

    try:
        save_library(bibliotheque, str(bib_json))
        print(f"Sauvegarde réussie : '{bib_json}'")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")

    try:
        export_library_csv(bibliotheque, str(bib_csv))
        print(f"Export CSV réussi : '{bib_csv}'")
    except Exception as e:
        print(f"Erreur lors de l'export CSV : {e}")

    try:
        bibliotheque_rechargee = load_library(str(bib_json))
        print("\nBibliotheque rechargee depuis JSON :")
        bibliotheque_rechargee.afficher()
    except Exception as e:
        print(f"Erreur lors du chargement : {e}")

if __name__ == "__main__":
    choice = _choose_mode()
    if choice == "2":
        run_gui()
    else:
        main()
