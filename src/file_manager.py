import json
import csv
from pathlib import Path
from typing import Optional

from .models import Livre, LivreNumerique, Bibliotheque
from .exceptions import ErreurFichier


class BibliothequeAvecFichier(Bibliotheque):
    """Extension de Bibliotheque avec operations de sauvegarde / chargement / export.

    Les methodes lèvent `ErreurFichier` en cas de probleme et n'effectuent pas de print.
    """

    def sauvegarder(self, filepath: str) -> None:
        p = Path(filepath)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            data = [livre.to_dict() for livre in self.livres]
            with p.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ErreurFichier(f"Impossible d'ecrire le fichier '{filepath}': {e}")

    def charger(self, filepath: str) -> None:
        p = Path(filepath)
        if not p.exists():
            raise ErreurFichier(f"Fichier '{filepath}' inexistant")
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ErreurFichier(f"Format JSON invalide dans '{filepath}': {e}")
        except Exception as e:
            raise ErreurFichier(f"Impossible de lire '{filepath}': {e}")

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
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
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
        except Exception as e:
            raise ErreurFichier(f"Impossible d'exporter CSV '{filepath}': {e}")
