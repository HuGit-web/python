import json
import csv
from pathlib import Path

class Livre:
    def __init__(self, titre, auteur, ISBN):
        self.titre = titre
        self.auteur = auteur
        self.ISBN = ISBN
    
    def to_dict(self):
        return{
            "type" : "Livre",
            "titre" : self.titre,
            "auteur" : self.auteur,
            "ISBN" : self.ISBN
        }

class LivreNumerique(Livre):
    def __init__(self, titre, auteur, ISBN, taille_fichier):
        super().__init__(titre, auteur, ISBN)
        self.taille_fichier = taille_fichier
    
    def to_dict(self):
        base = super().to_dict()
        base["type"] = "Livre Numerique"
        base["taille_fichier"] = self.taille_fichier
        return base

class Bibliotheque():
    def __init__(self, nom):
        self.nom = nom
        self.livres = []
    
    def ajouter_livre(self, livre):
        self.livres.append(livre)
        print(f"Livre '{livre.titre}' a été ajouté à notre très grande et somptueuse bibliothèque.")
    
    def supprimer_livre(self, ISBN):
        for livre in self.livres :
            if livre.ISBN == ISBN :
                self.livres.remove(livre)
                print(f"Livre '{livre.titre}' a malheureusement été supprimé de notre bibliothèque.")
                return
        print("Livre non trouvé...")
    
    def recherche_par_titre(self, titre):
        resultats = [livre for livre in self.livres if livre.titre == titre]
        return resultats
    
    def recherche_par_auteur(self, auteur):
        resultats = [livre for livre in self.livres if livre.auteur == auteur]
        return resultats
    
    # JSON
    def sauvegarder(self, filepath):
        try :
            data = [livre.to_dict() for livre in self.livres]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Sauvegarde dans '{filepath}' réussie")
        except Exception as e :
            print(f"Erreur lors de la sauvegarde : {e}")
    
    # Chargement
    def charger(self, filepath):
        try :
            with open(filepath, "r", encoding="utf-8") as f :
                data = json.load(f)
            self.livres.clear()
            for livre_dic in data :
                if livre_dic["type"] == "Livre Numerique":
                    livre = LivreNumerique(
                        livre_dic["titre"],
                        livre_dic["auteur"],
                        livre_dic["ISBN"],
                        livre_dic["taille_fichier"]
                    )
                else :
                    livre = Livre(
                        livre_dic["titre"],
                        livre_dic["auteur"],
                        livre_dic["ISBN"]
                    )
                self.livres.append(livre)
            print(f"Changement depuis '{filepath} réussi")
        except FileNotFoundError :
            print(f"Fichier '{filepath}' inexistant.")
        except json.JSONDecodeError:
            print("Format JSON invalide.")
        except Exception as e:
            print(f"Erreur lors du chargement : {e}")
    
    # CSV
    def export_csv(self, filepath):
        try:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["type", "titre", "auteur", "ISBN", "taille_fichier"])
                for livre in self.livres:
                    d = livre.to_dict()
                    writer.writerow([
                        d["type"], d["titre"], d["auteur"], d["ISBN"], d.get("taille_fichier", "")
                    ])
            print(f"Export CSV vers '{filepath}' réussi.")
        except IOError:
            print("Permissions insuffisantes ou chemin inaccessible.")
        except Exception as e:
            print(f"Erreur lors de l'export CSV : {e}")


# ====== Tests ======
livre1 = Livre("1984", "George Orwell", "ISBN123")
livre2 = Livre("Les Misérables", "Victor Hugo", "ISBN456")
livre3 = Livre("Le Petit Prince", "Antoine de Saint-Exupéry", "ISBN789")
livre4 = LivreNumerique("Digital Fortress", "Dan Brown", "ISBN101", "2MB")

ma_bibliotheque = Bibliotheque("La Bible aux Tchèques")

ma_bibliotheque.ajouter_livre(livre1)
ma_bibliotheque.ajouter_livre(livre2)
ma_bibliotheque.ajouter_livre(livre3)
ma_bibliotheque.ajouter_livre(livre4)

# Recherche par titre
resultats = ma_bibliotheque.recherche_par_titre("1984")
for livre in resultats:
    print(f"Trouvé : {livre.titre} par {livre.auteur}")

# Suppression
ma_bibliotheque.supprimer_livre("ISBN456")

# Recherches par auteur
resultats = ma_bibliotheque.recherche_par_auteur("Victor Hugo")
for livre in resultats:
    print(f"Trouvé : {livre.titre} par {livre.auteur}")

# Persistance et export (utilise dossier relatif `data/` du projet)
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(parents=True, exist_ok=True)
bib_path = data_dir / "bib.json"
csv_path = data_dir / "catalogue.csv"

ma_bibliotheque.sauvegarder(str(bib_path))
ma_bibliotheque.export_csv(str(csv_path))
ma_bibliotheque.charger(str(bib_path))  # Recharge le catalogue sauvegardé