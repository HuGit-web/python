# main.py

from pathlib import Path

# Bibliothèque (déjà existant)
from src.interface import (
    create_demo_library,
    save_library,
    load_library,
    export_library_csv
)

from src.gui import run_gui

# Chat application
from chat.server import start_server
from chat.client import start_client


def _choose_mode():
    print("\n====================================")
    print("       CHOISISSEZ LE MODE")
    print("====================================")
    print("1) Mode Démo (CLI)")
    print("2) Interface Graphique (Bibliothèque)")
    print("3) Démarrer le serveur de chat")
    print("4) Démarrer un client de chat")
    print("5) Quitter")
    print("====================================")
    return input("Votre choix : ").strip()


def main_cli():
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
    while True:
        choice = _choose_mode()

        if choice == "1":
            main_cli()

        elif choice == "2":
            run_gui()

        elif choice == "3":
            print("\n[Démarrage du serveur de chat...]")
            start_server()   # boucle infinie → CTRL+C pour arrêter

        elif choice == "4":
            print("\n[Démarrage du client de chat...]")
            start_client()

        elif choice == "5":
            print("\nFermeture du programme.")
            break

        else:
            print("Choix invalide, réessayez.")
