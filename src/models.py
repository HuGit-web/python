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

    def sauvegarder(self, filepath: str) -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = [livre.to_dict() for livre in self.livres]
        try:
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise OSError(f"Erreur ecriture fichier: {e}")

    def charger(self, filepath: str) -> None:
        p = Path(filepath)
        if not p.exists():
            raise FileNotFoundError(f"Fichier '{filepath}' inexistant")
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Format JSON invalide: {e}")
        except OSError as e:
            raise OSError(f"Erreur lecture fichier: {e}")

        self.livres.clear()
        for livre_dic in data:
            if livre_dic.get("type") == "Livre Numerique":
                livre = LivreNumerique(
                    livre_dic.get("titre", ""),
                    livre_dic.get("auteur", ""),
                    livre_dic.get("ISBN", ""),
                    livre_dic.get("taille_fichier", ""),
                )
            else:
                livre = Livre(
                    livre_dic.get("titre", ""),
                    livre_dic.get("auteur", ""),
                    livre_dic.get("ISBN", ""),
                )
            self.livres.append(livre)

    def export_csv(self, filepath: str) -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            with p.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["type", "titre", "auteur", "ISBN", "taille_fichier"])
                for livre in self.livres:
                    d = livre.to_dict()
                    writer.writerow([
                        d.get("type", ""),
                        d.get("titre", ""),
                        d.get("auteur", ""),
                        d.get("ISBN", ""),
                        d.get("taille_fichier", ""),
                    ])
        except OSError as e:
            raise OSError(f"Erreur export CSV: {e}")
