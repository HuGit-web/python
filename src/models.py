import json
import csv
from pathlib import Path
from typing import List

class Livre:
    def __init__(self, titre: str, auteur: str, ISBN: str):
        self.titre = titre
        self.auteur = auteur
        self.ISBN = ISBN

    def to_dict(self) -> dict:
        return {
            "type": "Livre",
            "titre": self.titre,
            "auteur": self.auteur,
            "ISBN": self.ISBN,
        }

    def __str__(self) -> str:
        return f"{self.titre} — {self.auteur} (ISBN: {self.ISBN})"

    def __repr__(self) -> str:
        return f"Livre(titre={self.titre!r}, auteur={self.auteur!r}, ISBN={self.ISBN!r})"

class LivreNumerique(Livre):
    def __init__(self, titre: str, auteur: str, ISBN: str, taille_fichier: str):
        super().__init__(titre, auteur, ISBN)
        self.taille_fichier = taille_fichier

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["type"] = "Livre Numerique"
        base["taille_fichier"] = self.taille_fichier
        return base

    def __str__(self) -> str:
        return f"{self.titre} — {self.auteur} (ISBN: {self.ISBN}, {self.taille_fichier})"

    def __repr__(self) -> str:
        return (f"LivreNumerique(titre={self.titre!r}, auteur={self.auteur!r}, "
                f"ISBN={self.ISBN!r}, taille_fichier={self.taille_fichier!r})")

class Bibliotheque:
    def __init__(self, nom: str):
        self.nom = nom
        self.livres: List[Livre] = []

    def ajouter_livre(self, livre: Livre) -> None:
        self.livres.append(livre)

    def afficher(self) -> None:
        """Affiche la liste des livres présents dans la bibliothèque."""
        if not self.livres:
            print(f"Bibliotheque '{self.nom}' est vide.")
            return
        print(f"Livres dans la bibliotheque '{self.nom}':")
        for i, livre in enumerate(self.livres, start=1):
            print(f" {i}. {livre}")

    def lister(self) -> list:
        """Retourne la liste des livres (objets)."""
        return list(self.livres)

    def supprimer_livre(self, ISBN: str) -> bool:
        for livre in list(self.livres):
            if livre.ISBN == ISBN:
                self.livres.remove(livre)
                return True
        return False

    def recherche_par_titre(self, titre: str):
        return [livre for livre in self.livres if livre.titre == titre]

    def recherche_par_auteur(self, auteur: str):
        return [livre for livre in self.livres if livre.auteur == auteur]
    # File IO responsibilities have been moved to `src.file_manager.BibliothequeAvecFichier`.
    # This keeps the domain model (Livre / Bibliotheque) focused on business logic.

    # Backwards-compatible wrappers that delegate to BibliothequeAvecFichier
    def sauvegarder(self, filepath: str) -> None:
        from .file_manager import BibliothequeAvecFichier
        b = BibliothequeAvecFichier(self.nom)
        b.livres = list(self.livres)
        return b.sauvegarder(filepath)

    def charger(self, filepath: str) -> None:
        from .file_manager import BibliothequeAvecFichier
        b = BibliothequeAvecFichier(self.nom)
        b.charger(filepath)
        self.livres = b.livres

    def export_csv(self, filepath: str) -> None:
        from .file_manager import BibliothequeAvecFichier
        b = BibliothequeAvecFichier(self.nom)
        b.livres = list(self.livres)
        return b.export_csv(filepath)

