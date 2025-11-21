import json
import csv
from pathlib import Path
from typing import List

class Livre:
    def __init__(self, titre: str, auteur: str, ISBN: str, exemplaire_id: str | None = None, etat: str = "disponible"):
        self.titre = titre
        self.auteur = auteur
        self.ISBN = ISBN
        # each physical copy can have an exemplaire id; if None, treated as a generic copy
        self.exemplaire_id = exemplaire_id
        # etat: disponible, emprunte, endommage, perdu
        self.etat = etat

    def to_dict(self) -> dict:
        return {
            "type": "Livre",
            "titre": self.titre,
            "auteur": self.auteur,
            "ISBN": self.ISBN,
            "exemplaire_id": self.exemplaire_id,
            "etat": self.etat,
            "history": getattr(self, "history", []),
        }

    def __str__(self) -> str:
        extra = f", id:{self.exemplaire_id}" if self.exemplaire_id else ""
        return f"{self.titre} — {self.auteur} (ISBN: {self.ISBN}{extra})"

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
        # each Livre instance may represent a physical exemplar (with exemplaire_id)
        self.livres: List[Livre] = []
        # reservation queues per ISBN (FIFO list of usernames)
        self.reservations: dict[str, list[str]] = {}

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

    def ajouter_exemplaire(self, titre: str, auteur: str, ISBN: str, exemplaire_id: str) -> None:
        l = Livre(titre, auteur, ISBN, exemplaire_id=exemplaire_id)
        self.livres.append(l)

    def trouver_exemplaires(self, ISBN: str) -> list:
        return [livre for livre in self.livres if livre.ISBN == ISBN]

    def emprunter_exemplaire(self, ISBN: str, user) -> Optional[Livre]:
        """Try to borrow an available exemplar for user. Returns the Livre borrowed or None."""
        # check reservation queue: if exists and first != user.username, user must reserve instead
        queue = self.reservations.get(ISBN, [])
        if queue and queue[0] != getattr(user, 'username', None):
            return None
        for livre in self.livres:
            if livre.ISBN == ISBN and livre.etat == "disponible":
                # mark borrowed tentatively
                livre.etat = "emprunte"
                # call user's borrow to create Loan (may raise if user cannot borrow)
                try:
                    loan = user.borrow(ISBN, exemplaire_id=livre.exemplaire_id)
                except Exception:
                    # restore state on failure and propagate a clean None so callers can show a message
                    livre.etat = "disponible"
                    return None
                # attach loan info to book history
                if not hasattr(livre, 'history'):
                    livre.history = []
                livre.history.append(loan.to_dict())
                # if user was first in queue, pop
                if queue and queue[0] == user.username:
                    queue.pop(0)
                return livre
        return None

    def retourner_exemplaire(self, exemplaire_id: str, user, users_file: str | None = None) -> Optional[float]:
        """Return an exemplar by id for the given user. Returns penalty amount if any."""
        # find the active loan for this user
        loan = None
        for l in user.loans:
            if l.exemplaire_id == exemplaire_id and l.date_retour_effective is None:
                loan = l
                break
        if loan is None:
            return None
        montant = user.return_loan(loan)
        # mark exemplar available
        for livre in self.livres:
            if livre.exemplaire_id == exemplaire_id:
                livre.etat = "disponible"
                # notify next reserver if any
                queue = self.reservations.get(livre.ISBN, [])
                if queue and users_file:
                    next_username = queue[0]
                    # notify via file_manager helper
                    from .file_manager import BibliothequeAvecFichier
                    BibliothequeAvecFichier.notifier_user(next_username, f"Livre disponible: {livre.titre}", users_file)
                break
        return montant

    def reserver_livre(self, ISBN: str, username: str = None, user_obj=None, users_file: str | None = None) -> bool:
        """Reserve book for username or user_obj. Updates both library queue and user's reservations if user_obj provided.

        Returns True if reservation added, False if already present.
        """
        if username is None and user_obj is not None:
            username = getattr(user_obj, 'username', None)
        if username is None:
            return False
        q = self.reservations.setdefault(ISBN, [])
        if username in q:
            return False
        q.append(username)
        # also update user's reservation list if provided
        if user_obj is not None:
            # create a reservation record on the user
            try:
                from .users import Reservation
                r = Reservation(ISBN, None, __import__('datetime').date.today())
                user_obj.reservations.append(r)
            except Exception:
                pass
            # persist users if path provided
            if users_file:
                from .file_manager import BibliothequeAvecFichier
                try:
                    BibliothequeAvecFichier.sauvegarder_users([user_obj] + [], users_file)
                except Exception:
                    # if saving just single user fails, ignore; caller may save full list
                    pass
        return True

    def annuler_reservation(self, ISBN: str, username: str = None, user_obj=None, users_file: str | None = None) -> bool:
        if username is None and user_obj is not None:
            username = getattr(user_obj, 'username', None)
        if username is None:
            return False
        q = self.reservations.get(ISBN, [])
        removed = False
        if username in q:
            q.remove(username)
            removed = True
        # remove from user_obj reservations
        if user_obj is not None:
            try:
                # remove first matching reservation for this ISBN
                for i, r in enumerate(list(user_obj.reservations)):
                    if getattr(r, 'isbn', None) == ISBN:
                        user_obj.reservations.pop(i)
                        break
            except Exception:
                pass
            if users_file:
                from .file_manager import BibliothequeAvecFichier
                try:
                    BibliothequeAvecFichier.sauvegarder_users([user_obj] + [], users_file)
                except Exception:
                    pass
        return removed

    def get_reservations(self, ISBN: str) -> list:
        return list(self.reservations.get(ISBN, []))

    def recherche_par_titre(self, titre: str):
        return [livre for livre in self.livres if livre.titre == titre]

    def recherche_par_auteur(self, auteur: str):
        return [livre for livre in self.livres if livre.auteur.lower() == auteur.lower()]
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

