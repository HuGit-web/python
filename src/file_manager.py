import json
import csv
from pathlib import Path
from typing import Optional
import tempfile
import os

from .models import AggregatedLivre, LivreNumerique, Bibliotheque
from .exceptions import ErreurFichier
from .users import User


class BibliothequeAvecFichier(Bibliotheque):
    """Extension de Bibliotheque avec operations de sauvegarde / chargement / export.

    Les methodes lèvent `ErreurFichier` en cas de probleme et n'effectuent pas de print.
    """

    def sauvegarder(self, filepath: str) -> None:
        p = Path(filepath)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            
            from collections import defaultdict
            counts = defaultdict(int)
            avail = defaultdict(int)
            for livre in self.livres:
                isbn = str(getattr(livre, 'ISBN', '') or '')
                total = int(getattr(livre, 'nb_exemplaire', 1))
                disp = int(getattr(livre, 'disponibles', total))
                counts[isbn] += total
                avail[isbn] += disp

            exemplaires_map = {isbn: {"total": counts[isbn], "disponibles": avail[isbn]} for isbn in counts}

            data = {
                "livres": [livre.to_dict() for livre in self.livres],
                "reservations": getattr(self, "reservations", {}),
                "exemplaires": exemplaires_map,
            }
            dirpath = str(p.parent)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dirpath, delete=False) as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                tf.flush()
                os.fsync(tf.fileno())
            os.replace(tf.name, str(p))
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
        livres_data = data.get("livres") if isinstance(data, dict) else data
        for livre_dic in livres_data:
            
            exmap = livre_dic.get('exemplaires') or livre_dic.get('exemplaires_map')
            if livre_dic.get("type") == "Livre Numerique":
                livre = LivreNumerique(
                    livre_dic.get("titre", ""),
                    livre_dic.get("auteur", ""),
                    livre_dic.get("ISBN", ""),
                    livre_dic.get("taille_fichier", ""),
                )
                if livre_dic.get("genre"):
                    livre.genre = livre_dic.get("genre")
                try:
                    livre.reviews = livre_dic.get("reviews", []) or []
                except Exception:
                    livre.reviews = []
                
                self.livres.append(livre)
                continue

            if isinstance(exmap, dict):
                total = int(exmap.get('total', 1))
                disponibles = int(exmap.get('disponibles', total))
            else:
                
                total = livre_dic.get('nb_exemplaire') or 1
                disponibles = livre_dic.get('disponibles') if 'disponibles' in livre_dic else total

            livre = AggregatedLivre(
                livre_dic.get("titre", ""),
                livre_dic.get("auteur", ""),
                livre_dic.get("ISBN", ""),
                total=int(total),
                disponibles=int(disponibles),
            )
            if livre_dic.get("genre"):
                livre.genre = livre_dic.get("genre")
            try:
                livre.reviews = livre_dic.get("reviews", []) or []
            except Exception:
                livre.reviews = []
            if livre_dic.get("history"):
                try:
                    livre.history = livre_dic.get("history", [])
                except Exception:
                    livre.history = []
            
            if livre_dic.get('exemplaires_details'):
                try:
                    livre.exemplaires_details = list(livre_dic.get('exemplaires_details', []))
                except Exception:
                    livre.exemplaires_details = []
            self.livres.append(livre)

        self.reservations = {}
        if isinstance(data, dict):
            res = data.get("reservations")
            if isinstance(res, dict):
                for k, v in res.items():
                    self.reservations[k] = list(v)
            
            ex_map = data.get("exemplaires")
            if isinstance(ex_map, dict):
                
                self.exemplaires = {str(k): v for k, v in ex_map.items()}
            else:
                self.exemplaires = {}
        else:
            self.exemplaires = {}

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

    @staticmethod
    def sauvegarder_users(users: list, filepath: str) -> None:
        p = Path(filepath)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            data = [u.to_dict() for u in users]
            dirpath = str(p.parent)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dirpath, delete=False) as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                tf.flush()
                os.fsync(tf.fileno())
            os.replace(tf.name, str(p))
        except Exception as e:
            raise ErreurFichier(f"Impossible d'ecrire le fichier users '{filepath}': {e}")

    @staticmethod
    def charger_users(filepath: str) -> list:
        p = Path(filepath)
        if not p.exists():
            return []
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ErreurFichier(f"Format JSON invalide dans users '{filepath}': {e}")
        except Exception as e:
            raise ErreurFichier(f"Impossible de lire users '{filepath}': {e}")
        users = []
        for ud in data:
            try:
                users.append(User.from_dict(ud))
            except Exception:
                continue
        return users

    @staticmethod
    def notifier_user(username: str, message: str, users_filepath: str) -> None:
        try:
            users = BibliothequeAvecFichier.charger_users(users_filepath)
        except ErreurFichier:
            users = []
        updated = False
        for u in users:
            if getattr(u, 'username', None) == username:
                u.notifications.append(message)
                updated = True
                break
        if not updated:
            from .users import User
            new = User(username, "")
            new.notifications.append(message)
            users.append(new)
        BibliothequeAvecFichier.sauvegarder_users(users, users_filepath)

    def sauvegarder_transactionnel(self, users: list, bib_filepath: str, users_filepath: str) -> None:
        bib_p = Path(bib_filepath)
        users_p = Path(users_filepath)
        try:
            bib_p.parent.mkdir(parents=True, exist_ok=True)
            users_p.parent.mkdir(parents=True, exist_ok=True)

            from collections import defaultdict
            counts = defaultdict(int)
            avail = defaultdict(int)
            for livre in self.livres:
                isbn = str(getattr(livre, 'ISBN', '') or '')
                total = int(getattr(livre, 'nb_exemplaire', 1))
                disp = int(getattr(livre, 'disponibles', total))
                counts[isbn] += total
                avail[isbn] += disp
            exemplaires_map = {isbn: {"total": counts[isbn], "disponibles": avail[isbn]} for isbn in counts}

            bib_data = {
                "livres": [livre.to_dict() for livre in self.livres],
                "reservations": getattr(self, "reservations", {}),
                "exemplaires": exemplaires_map,
            }
            users_data = [u.to_dict() for u in users]

            bib_dir = str(bib_p.parent)
            users_dir = str(users_p.parent)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=bib_dir, delete=False) as tf_bib:
                json.dump(bib_data, tf_bib, ensure_ascii=False, indent=2)
                tf_bib.flush(); os.fsync(tf_bib.fileno())
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=users_dir, delete=False) as tf_users:
                json.dump(users_data, tf_users, ensure_ascii=False, indent=2)
                tf_users.flush(); os.fsync(tf_users.fileno())

            os.replace(tf_bib.name, str(bib_p))
            os.replace(tf_users.name, str(users_p))
        except Exception as e:
            try:
                if 'tf_bib' in locals() and tf_bib and Path(tf_bib.name).exists():
                    os.remove(tf_bib.name)
            except Exception:
                pass
            try:
                if 'tf_users' in locals() and tf_users and Path(tf_users.name).exists():
                    os.remove(tf_users.name)
            except Exception:
                pass
            raise ErreurFichier(f"Erreur lors de la sauvegarde transactionnelle: {e}")

    def reconcile_reservations(self, users: list, persist: bool = False, users_path: str | None = None, bib_path: str | None = None) -> None:
        """Reconcile reservation queues between the library and the provided users list.

        - Remove usernames from bibliotheque.reservations that are not present in users.
        - Ensure each user's reservations are represented in bibliotheque.reservations.
        If persist is True, save both users and bib to provided paths (users_path, bib_path).
        """
        valid_usernames = {getattr(u, 'username', None) for u in users}
        for isbn, queue in list(getattr(self, 'reservations', {}).items()):
            newq = [u for u in queue if u in valid_usernames]
            self.reservations[isbn] = newq
        for u in users:
            for r in getattr(u, 'reservations', []):
                isbn = getattr(r, 'isbn', None)
                if not isbn:
                    continue
                q = self.reservations.setdefault(isbn, [])
                if u.username not in q:
                    q.append(u.username)
        if persist:
            if users_path:
                BibliothequeAvecFichier.sauvegarder_users(users, users_path)
            if bib_path:
                self.sauvegarder(bib_path)
