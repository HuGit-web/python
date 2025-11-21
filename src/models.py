import json
import csv
from pathlib import Path
from typing import List, Optional


class AggregatedLivre:
    
    def __init__(self, titre: str, auteur: str, ISBN: str, total: int = 0, disponibles: int = 0, genre: str | None = None):
        self.type = "Livre"
        self.titre = titre
        self.auteur = auteur
        # Normalize ISBN to avoid mismatches due to surrounding whitespace
        self.ISBN = ISBN.strip() if isinstance(ISBN, str) else (str(ISBN) if ISBN is not None else "")
        self.nb_exemplaire = int(total)
        self.disponibles = int(disponibles)
        self.genre = genre
        self.reviews: list[dict] = []
        self.history: list[dict] = []
        self.exemplaires_details: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "titre": self.titre,
            "auteur": self.auteur,
            "ISBN": self.ISBN,
            "exemplaire_id": None,
            "etat": "disponible" if self.disponibles > 0 else "indisponible",
            "genre": self.genre,
            "reviews": list(self.reviews),
            "history": list(self.history),
            "exemplaires": {"total": int(self.nb_exemplaire), "disponibles": int(self.disponibles)},
            "exemplaires_details": list(self.exemplaires_details),
        }

    def __repr__(self) -> str:
        return f"AggregatedLivre(ISBN={self.ISBN!r}, total={self.nb_exemplaire}, disponibles={self.disponibles})"


class LivreNumerique(AggregatedLivre):
    def __init__(self, titre: str, auteur: str, ISBN: str, taille_fichier: str):
        super().__init__(titre, auteur, ISBN)
        self.type = "Livre Numerique"
        self.taille_fichier = taille_fichier

    def to_dict(self) -> dict:
        d = super().to_dict()
        d['taille_fichier'] = getattr(self, 'taille_fichier', None)
        return d


Livre = AggregatedLivre


class Bibliotheque:
    def __init__(self, nom: str):
        self.nom = nom
        self.livres: List[AggregatedLivre] = []
        self.reservations: dict[str, list[str]] = {}

    def ajouter_livre(self, livre: Livre) -> None:
        
        if isinstance(livre, AggregatedLivre):
            self.livres.append(livre)
            return
        
        try:
            titre = livre.get('titre')
            auteur = livre.get('auteur')
            isbn = livre.get('ISBN')
            exemplaires = livre.get('exemplaires', {})
            total = exemplaires.get('total', 1)
            dispon = exemplaires.get('disponibles', total)
        except Exception:
            return
        ag = AggregatedLivre(titre, auteur, isbn, total=int(total), disponibles=int(dispon))
        if 'exemplaires_details' in livre:
            ag.exemplaires_details = list(livre.get('exemplaires_details', []))
        self.livres.append(ag)

    def afficher(self) -> None:
        
        if not self.livres:
            print(f"Bibliotheque '{self.nom}' est vide.")
            return
        print(f"Livres dans la bibliotheque '{self.nom}':")
        for i, livre in enumerate(self.livres, start=1):
            print(f" {i}. {livre}")

    def lister(self) -> list:
        return list(self.livres)

    def supprimer_livre(self, ISBN: str) -> bool:
        for livre in list(self.livres):
            if livre.ISBN == ISBN:
                self.livres.remove(livre)
                return True
        return False

    def ajouter_exemplaire(self, titre: str, auteur: str, ISBN: str, exemplaire_id: str, genre: str | None = None) -> None:
        if not ISBN:
            return
        ag = None
        for livre in self.livres:
            if getattr(livre, 'ISBN', None) == ISBN:
                ag = livre
                break
        if ag is None:
            
            ag = AggregatedLivre(titre, auteur, ISBN, total=1, disponibles=1)
            if genre:
                ag.genre = genre
            if exemplaire_id:
                ag.exemplaires_details.append({'exemplaire_id': exemplaire_id, 'etat': 'disponible'})
            else:
                
                from uuid import uuid4
                ag.exemplaires_details.append({'exemplaire_id': f"{ISBN}-ex{uuid4().hex[:8]}", 'etat': 'disponible'})
            self.livres.append(ag)
            return

        
        ag.nb_exemplaire = int(getattr(ag, 'nb_exemplaire', 0)) + 1
        ag.disponibles = int(getattr(ag, 'disponibles', 0)) + 1
        if genre:
            try:
                ag.genre = genre
            except Exception:
                pass
        if exemplaire_id:
            ag.exemplaires_details.append({'exemplaire_id': exemplaire_id, 'etat': 'disponible'})
        else:
            from uuid import uuid4
            ag.exemplaires_details.append({'exemplaire_id': f"{ISBN}-ex{uuid4().hex[:8]}", 'etat': 'disponible'})
        ag.disponibles = min(ag.disponibles, ag.nb_exemplaire)

    def trouver_exemplaires(self, ISBN: str) -> list:
        return [liv for liv in self.livres if getattr(liv, 'ISBN', None) == ISBN]

    def emprunter_exemplaire(self, ISBN: str, user) -> Optional[Livre]:
        
        queue = self.reservations.get(ISBN, [])
        username = getattr(user, 'username', None)
        if queue and queue[0] != username:
            raise ValueError("Une réservation existe et vous n'êtes pas en tête de file")
        for livre in self.livres:
            if getattr(livre, 'ISBN', None) != ISBN:
                continue

            # If per-exemplar details exist, select an available exemplar
            details = getattr(livre, 'exemplaires_details', []) or []
            if details:
                found = None
                for d in details:
                    if str(d.get('etat', 'disponible')).lower() == 'disponible':
                        found = d
                        break
                if found is None:
                    # no available exemplar in details
                    continue

                # mark exemplar as borrowed
                exid = found.get('exemplaire_id')
                found['etat'] = 'emprunte'
                livre.disponibles = max(0, int(getattr(livre, 'disponibles', 0)) - 1)
                try:
                    loan = user.borrow(ISBN, exid)
                except Exception:
                    # revert on failure
                    found['etat'] = 'disponible'
                    livre.disponibles = min(livre.nb_exemplaire, int(getattr(livre, 'disponibles', 0)) + 1)
                    raise

                entry = {}
                try:
                    entry = loan.to_dict()
                    entry['username'] = username
                except Exception:
                    entry = {'username': username}
                livre.history.append(entry)
                if queue and queue[0] == username:
                    queue.pop(0)
                return livre

            # No per-exemplar details present; fall back to aggregate behavior but synthesize an exemplar
            if int(getattr(livre, 'disponibles', 0)) <= 0:
                continue

            # synthesize an exemplar id and record it in details so future returns find it
            synth_idx = len(getattr(livre, 'history', [])) + 1
            exid = f"{ISBN}-synth{synth_idx}"
            try:
                livre.exemplaires_details.append({'exemplaire_id': exid, 'etat': 'emprunte'})
            except Exception:
                livre.exemplaires_details = [{'exemplaire_id': exid, 'etat': 'emprunte'}]
            livre.nb_exemplaire = max(int(getattr(livre, 'nb_exemplaire', 0)), len(livre.exemplaires_details))
            livre.disponibles = max(0, int(getattr(livre, 'disponibles', 0)) - 1)
            try:
                loan = user.borrow(ISBN, exid)
            except Exception:
                # revert synthesized detail
                try:
                    if livre.exemplaires_details and livre.exemplaires_details[-1].get('exemplaire_id') == exid:
                        livre.exemplaires_details.pop()
                except Exception:
                    pass
                livre.disponibles = min(livre.nb_exemplaire, int(getattr(livre, 'disponibles', 0)) + 1)
                raise

            entry = {}
            try:
                entry = loan.to_dict()
                entry['username'] = username
            except Exception:
                entry = {'username': username}
            livre.history.append(entry)
            if queue and queue[0] == username:
                queue.pop(0)
            return livre

        raise ValueError("Aucun exemplaire disponible pour cet ISBN")

    def retourner_exemplaire(self, exemplaire_id: str, user, users_file: str | None = None) -> Optional[float]:
        
        loan = None
        for l in getattr(user, 'loans', []):
            if getattr(l, 'exemplaire_id', None) == exemplaire_id and getattr(l, 'date_retour_effective', None) is None:
                loan = l
                break
        if loan is None:
            return None
        montant = user.return_loan(loan)

        isbn = getattr(loan, 'isbn', None) or getattr(loan, 'ISBN', None)
        if isbn is None:
            return montant
        for livre in self.livres:
            if getattr(livre, 'ISBN', None) == isbn:
                # try to mark the matching exemplar detail as available again
                updated_detail = False
                for d in getattr(livre, 'exemplaires_details', []):
                    if d.get('exemplaire_id') == exemplaire_id:
                        # only set to disponible if not endommagé/perdu
                        if str(d.get('etat', '')).lower() in ('emprunte', 'emprunt'):
                            d['etat'] = 'disponible'
                        updated_detail = True
                        break

                # update aggregate available count
                if updated_detail:
                    # recompute disponibles from details to be safe
                    try:
                        livre.disponibles = sum(1 for d in getattr(livre, 'exemplaires_details', []) if str(d.get('etat', 'disponible')).lower() == 'disponible')
                    except Exception:
                        livre.disponibles = min(livre.nb_exemplaire, int(getattr(livre, 'disponibles', 0)) + 1)
                else:
                    livre.disponibles = min(livre.nb_exemplaire, int(getattr(livre, 'disponibles', 0)) + 1)
                queue = self.reservations.get(livre.ISBN, [])
                if queue and users_file:
                    next_username = queue[0]
                    from .file_manager import BibliothequeAvecFichier
                    BibliothequeAvecFichier.notifier_user(next_username, f"Livre disponible: {livre.titre}", users_file)
                break
        return montant

    def reserver_livre(self, ISBN: str, username: str = None, user_obj=None, users_file: str | None = None) -> bool:
        
        if username is None and user_obj is not None:
            username = getattr(user_obj, 'username', None)
        if username is None:
            return False
        q = self.reservations.setdefault(ISBN, [])
        if username in q:
            return False
        # Allow pre-reservations even if copies are currently available.
        # (Previously reservations were only allowed when disponibles == 0.)
        # Append username to reservation queue.
        q.append(username)
        if user_obj is not None:
            try:
                from .users import Reservation
                r = Reservation(ISBN, None, __import__('datetime').date.today())
                user_obj.reservations.append(r)
            except Exception:
                pass
            # If a users file path is provided, update the persisted users list
            # by loading existing users, updating/adding this user, then saving.
            if users_file:
                try:
                    from .file_manager import BibliothequeAvecFichier
                    existing = BibliothequeAvecFichier.charger_users(users_file)
                    updated = False
                    for i, u in enumerate(existing):
                        if getattr(u, 'username', None) == username:
                            existing[i] = user_obj
                            updated = True
                            break
                    if not updated:
                        existing.append(user_obj)
                    BibliothequeAvecFichier.sauvegarder_users(existing, users_file)
                except Exception:
                    pass
        return True

    def add_review(self, ISBN: str, username: str, rating: int, comment: str | None = None) -> bool:
        
        for livre in self.livres:
            if livre.ISBN == ISBN:
                if not hasattr(livre, 'reviews'):
                    livre.reviews = []
                livre.reviews.append({
                    "username": username,
                    "rating": int(rating),
                    "comment": comment,
                })
                return True
        return False

    def recommend_for_user(self, user, limit: int = 6) -> list:
        
        genres = []

        for l in getattr(user, 'loans', []):
            for livre in self.livres:
                if livre.ISBN == l.isbn and getattr(livre, 'genre', None):
                    genres.append(livre.genre)

        for livre in self.livres:
            for h in getattr(livre, 'history', []):
                if h.get('username') == getattr(user, 'username', None) and livre.genre:
                    genres.append(livre.genre)

        from collections import Counter
        c = Counter(genres)
        fav_genres = [g for g, _ in c.most_common()]

        recs = []
        added_isbns = set()
        seen_isbns = {l.isbn for l in getattr(user, 'loans', [])}

        if not fav_genres:
            for lv in self.livres:
                isbn = getattr(lv, 'ISBN', None)
                if not isbn:
                    continue
                if isbn in seen_isbns or isbn in added_isbns:
                    continue
                if getattr(lv, 'disponibles', 0) <= 0:
                    continue
                recs.append(lv)
                added_isbns.add(isbn)
                if len(recs) >= limit:
                    break
            return recs

        for g in fav_genres:
            for livre in self.livres:
                isbn = getattr(livre, 'ISBN', None)
                if not isbn:
                    continue
                if getattr(livre, 'genre', None) != g:
                    continue
                if isbn in seen_isbns or isbn in added_isbns:
                    continue
                recs.append(livre)
                added_isbns.add(isbn)
                if len(recs) >= limit:
                    return recs
        return recs

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
        if user_obj is not None:
            try:
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

    def stats(self, users: list | None = None) -> dict:
        
        from collections import Counter, defaultdict
        res: dict = {}
        
        hist_counts = Counter()
        title_map = {}
        for livre in self.livres:
            title_map[livre.ISBN] = getattr(livre, 'titre', None)
            hist_counts[livre.ISBN] += len(getattr(livre, 'history', []))
        popular = [(isbn, title_map.get(isbn), cnt) for isbn, cnt in hist_counts.most_common()]
        res['popular_books'] = popular

        
        
        isbn_counts = Counter()
        status_counts = Counter()
        for livre in self.livres:
            isbn_counts[livre.ISBN] += int(getattr(livre, 'nb_exemplaire', 0))
            dispo = int(getattr(livre, 'disponibles', 0))
            emprunte = max(0, int(getattr(livre, 'nb_exemplaire', 0)) - dispo)
            status_counts['disponible'] += dispo
            status_counts['emprunte'] += emprunte
        res['multi_exemplaires'] = dict(isbn_counts)
        res['exemplar_status_counts'] = dict(status_counts)

        
        active_users = 0
        overdue = 0
        if users:
            for u in users:
                active = any(l.date_retour_effective is None for l in getattr(u, 'loans', []))
                if active:
                    active_users += 1
                for l in getattr(u, 'loans', []):
                    if l.date_retour_effective is None and getattr(l, 'date_retour_prevue', None) and l.date_retour_prevue < __import__('datetime').date.today():
                        overdue += 1
        res['active_users'] = active_users
        res['overdue_loans'] = overdue
        return res

    def set_exemplaire_status(self, exemplaire_id: str, status: str) -> bool:
        
        for livre in self.livres:
            
            for d in getattr(livre, 'exemplaires_details', []):
                if d.get('exemplaire_id') == exemplaire_id:
                    old = d.get('etat', 'disponible')
                    new = status
                    d['etat'] = new
                    
                    if old == 'disponible' and new != 'disponible':
                        livre.disponibles = max(0, livre.disponibles - 1)
                    elif old != 'disponible' and new == 'disponible':
                        livre.disponibles = min(livre.nb_exemplaire, livre.disponibles + 1)
                    return True
        return False

    def get_exemplar_statuses(self, ISBN: str) -> dict:
        
        from collections import Counter
        for livre in self.livres:
            if getattr(livre, 'ISBN', None) == ISBN:
                details = getattr(livre, 'exemplaires_details', None)
                if details:
                    c = Counter()
                    for d in details:
                        st = d.get('etat', 'disponible')
                        c[st] += 1
                    c['total'] = sum(c.values())
                    return dict(c)
                empruntes = max(0, int(livre.nb_exemplaire) - int(livre.disponibles))
                return {'disponible': int(livre.disponibles), 'emprunte': int(empruntes), 'total': int(livre.nb_exemplaire)}
        return {'disponible': 0, 'emprunte': 0, 'total': 0}

    def find_exemplar_by_id(self, exemplaire_id: str):
        
        for livre in self.livres:
            for d in getattr(livre, 'exemplaires_details', []):
                if d.get('exemplaire_id') == exemplaire_id:
                    
                    from types import SimpleNamespace
                    obj = SimpleNamespace(**d)
                    
                    obj.ISBN = getattr(livre, 'ISBN', None)
                    obj.titre = getattr(livre, 'titre', None)
                    return obj
        return None

    def ajouter_exemplaires_bulk(self, titre: str, auteur: str, ISBN: str, count: int) -> int:
        
        
        added = int(count)
        ag = None
        for livre in self.livres:
            if getattr(livre, 'ISBN', None) == ISBN:
                ag = livre
                break
        if ag is None:
            ag = AggregatedLivre(titre, auteur, ISBN, total=added, disponibles=added)
            
            from uuid import uuid4
            for _ in range(added):
                ag.exemplaires_details.append({'exemplaire_id': f"{ISBN}-ex{uuid4().hex[:8]}", 'etat': 'disponible'})
            self.livres.append(ag)
            return added
        
        from uuid import uuid4
        for _ in range(added):
            ag.nb_exemplaire += 1
            ag.disponibles += 1
            ag.exemplaires_details.append({'exemplaire_id': f"{ISBN}-ex{uuid4().hex[:8]}", 'etat': 'disponible'})
        
        ag.disponibles = min(ag.disponibles, ag.nb_exemplaire)
        return added

    def ensure_min_exemplaires_for_all(self, min_count: int = 5) -> int:
        
        total_added = 0
        for livre in self.livres:
            if getattr(livre, 'nb_exemplaire', 0) < min_count:
                need = int(min_count - livre.nb_exemplaire)
                if need > 0:
                    total_added += self.ajouter_exemplaires_bulk(livre.titre, livre.auteur, livre.ISBN, need)
        return total_added

    def trim_exemplaires(self, max_per_isbn: int = 5) -> int:
        
        
        removed = 0
        for livre in self.livres:
            if livre.nb_exemplaire > max_per_isbn:
                to_remove = int(livre.nb_exemplaire - max_per_isbn)
                
                livre.exemplaires_details = livre.exemplaires_details[:-to_remove] if len(livre.exemplaires_details) >= to_remove else []
                livre.nb_exemplaire = max_per_isbn
                livre.disponibles = min(livre.disponibles, livre.nb_exemplaire)
                removed += to_remove
        return removed

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

