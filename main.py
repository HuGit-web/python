from pathlib import Path
from src.interface import (
    create_demo_library,
    save_library,
    load_library,
    export_library_csv
)

def main() -> None:
    project_root = Path(__file__).resolve().parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    bib_json = data_dir / "bibliotheque.json"
    bib_csv = data_dir / "bibliotheque.csv"

    bibliotheque = create_demo_library()
    print("Bibliothèque de démonstration créée :")
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
        print("\nBibliothèque rechargée depuis JSON :")
        bibliotheque_rechargee.afficher()
    except Exception as e:
        print(f"Erreur lors du chargement : {e}")

if __name__ == "__main__":
    main()
