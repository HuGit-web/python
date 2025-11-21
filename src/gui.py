import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional

from .file_manager import BibliothequeAvecFichier
from .models import Livre
from .users import User


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "bib.json"
USERS_FILE = DATA_DIR / "users.json"


class BibliothequeApp(tk.Tk):
    def __init__(self, data_file: Path = DATA_FILE, users_file: Path = USERS_FILE):
        super().__init__()
        self.title("Gestionnaire de bibliotheque")
        self.geometry("1100x600")
        self.resizable(True, True)

        self.data_file = data_file
        self.users_file = users_file
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.biblio = BibliothequeAvecFichier("Mes livres")
        try:
            if self.data_file.exists():
                self.biblio.charger(str(self.data_file))
        except Exception:
            pass

        try:
            self.users = BibliothequeAvecFichier.charger_users(str(self.users_file))
        except Exception:
            self.users = []

        try:
            self.biblio.reconcile_reservations(self.users, persist=True, users_path=str(self.users_file), bib_path=str(self.data_file))
        except Exception:
            pass

        self.current_user: Optional[User] = None

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        btn_login = ttk.Button(top, text="Se connecter", command=self._show_login)
        btn_login.pack(side=tk.LEFT, padx=4)

        btn_register = ttk.Button(top, text="S'inscrire", command=self._show_register)
        btn_register.pack(side=tk.LEFT, padx=4)

        btn_refresh = ttk.Button(top, text="Rafraîchir livres", command=self._refresh_list)
        btn_refresh.pack(side=tk.LEFT, padx=4)

        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        searchfrm = ttk.Frame(left)
        searchfrm.pack(fill=tk.X)
        ttk.Label(searchfrm, text="Rechercher par auteur:").pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(searchfrm, width=30)
        self.entry_search.pack(side=tk.LEFT, padx=6)
        ttk.Button(searchfrm, text="Rechercher", command=self._on_search).pack(side=tk.LEFT, padx=4)

        cols = ("#", "Titre", "Auteur", "ISBN", "Exemplaire", "Etat")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.pack(fill=tk.BOTH, expand=True)

        books_action_frame = ttk.Frame(left)
        books_action_frame.pack(fill=tk.X, pady=6)
        ttk.Button(books_action_frame, text="Emprunter le livre sélectionné", command=self._borrow_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(books_action_frame, text="Réserver le livre sélectionné", command=self._reserve_selected).pack(side=tk.LEFT, padx=4)
        self.admin_frame = ttk.Frame(left)
        self.admin_frame.pack(fill=tk.X, pady=6)
        ttk.Button(self.admin_frame, text="Ajouter exemplaire", command=self._admin_add_exemplar).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Supprimer livre (ISBN)", command=self._admin_delete_by_isbn).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Marquer exemplaire endommagé", command=self._admin_mark_damaged).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Stats bibliothèque", command=self._admin_show_stats).pack(side=tk.LEFT, padx=4)

        right = ttk.Frame(self, width=340)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=8)
        ttk.Label(right, text="Utilisateur connecté:").pack(anchor=tk.W)
        self.lbl_user = ttk.Label(right, text="(aucun)")
        self.lbl_user.pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(right, text="Prêts en cours:").pack(anchor=tk.W)
        self.lst_loans = tk.Listbox(right, height=8)
        self.lst_loans.pack(fill=tk.X)
        ttk.Button(right, text="Rendre sélection", command=self._return_selected).pack(fill=tk.X, pady=4)

        ttk.Label(right, text="Réservations:").pack(anchor=tk.W)
        self.lst_res = tk.Listbox(right, height=6)
        self.lst_res.pack(fill=tk.X)
        ttk.Button(right, text="Annuler réservation sélectionnée", command=self._cancel_reservation).pack(fill=tk.X, pady=4)

        ttk.Label(right, text="Pénalités (€):").pack(anchor=tk.W)
        self.lbl_pen = ttk.Label(right, text="0.00")
        self.lbl_pen.pack(anchor=tk.W)
        ttk.Button(right, text="Payer pénalités", command=self._pay_penalties).pack(fill=tk.X, pady=6)

    # ---------------- User management ----------------
    def _show_login(self):
        dlg = tk.Toplevel(self)
        dlg.title("Se connecter")
        ttk.Label(dlg, text="Nom d'utilisateur:").grid(column=0, row=0, sticky=tk.W, padx=6, pady=6)
        e_user = ttk.Entry(dlg)
        e_user.grid(column=1, row=0, padx=6)
        ttk.Label(dlg, text="Mot de passe:").grid(column=0, row=1, sticky=tk.W, padx=6, pady=6)
        e_pwd = ttk.Entry(dlg, show="*")
        e_pwd.grid(column=1, row=1, padx=6)

        def do_login():
            uname = e_user.get().strip()
            pwd = e_pwd.get().strip()
            for u in self.users:
                if u.username == uname and u.check_password(pwd):
                    self.current_user = u
                    self._on_login()
                    dlg.destroy()
                    return
            messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe invalide")

        ttk.Button(dlg, text="Se connecter", command=do_login).grid(column=0, row=2, columnspan=2, pady=8)

    def _show_register(self):
        dlg = tk.Toplevel(self)
        dlg.title("S'inscrire")
        ttk.Label(dlg, text="Nom d'utilisateur:").grid(column=0, row=0, sticky=tk.W, padx=6, pady=6)
        e_user = ttk.Entry(dlg)
        e_user.grid(column=1, row=0, padx=6)
        ttk.Label(dlg, text="Mot de passe:").grid(column=0, row=1, sticky=tk.W, padx=6, pady=6)
        e_pwd = ttk.Entry(dlg, show="*")
        e_pwd.grid(column=1, row=1, padx=6)
        ttk.Label(dlg, text="Abonnement (basique/premium/VIP):").grid(column=0, row=2, sticky=tk.W, padx=6, pady=6)
        e_sub = ttk.Entry(dlg)
        e_sub.insert(0, "basique")
        e_sub.grid(column=1, row=2, padx=6)

        def do_register():
            uname = e_user.get().strip()
            pwd = e_pwd.get().strip()
            sub = e_sub.get().strip() or "basique"
            if not uname or not pwd:
                messagebox.showwarning("Champs manquants", "Remplissez nom et mot de passe")
                return
            if any(u.username == uname for u in self.users):
                messagebox.showwarning("Existe", "Nom d'utilisateur déjà utilisé")
                return
            new = User.create(uname, pwd, subscription_type=sub)
            self.users.append(new)
            BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
            messagebox.showinfo("Ok", "Compte créé. Connectez-vous.")
            dlg.destroy()

        ttk.Button(dlg, text="S'inscrire", command=do_register).grid(column=0, row=3, columnspan=2, pady=8)

    def _on_login(self):
        if not self.current_user:
            return
        self.lbl_user.config(text=self.current_user.username + (" (admin)" if self.current_user.is_admin else ""))
        # show notifications
        if getattr(self.current_user, 'notifications', None):
            msgs = "\n".join(self.current_user.notifications)
            messagebox.showinfo("Notifications", msgs)
            # clear them and persist
            self.current_user.notifications.clear()
            BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        self._refresh_user_panel()
        # show/hide admin frame
        if self.current_user and self.current_user.is_admin:
            self.admin_frame.pack(fill=tk.X, pady=6)
        else:
            self.admin_frame.forget()

    # ---------------- Book actions ----------------
    def _on_search(self):
        auteur = self.entry_search.get().strip()
        if not auteur:
            self._refresh_list()
            return
        resultats = self.biblio.recherche_par_auteur(auteur)
        self._populate_tree(resultats)

    def _refresh_list(self):
        self._populate_tree(self.biblio.lister())
        self._refresh_user_panel()

    def _populate_tree(self, livres):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, livre in enumerate(livres, start=1):
            ex_id = getattr(livre, 'exemplaire_id', '')
            etat = getattr(livre, 'etat', 'disponible')
            self.tree.insert("", tk.END, values=(idx, livre.titre, livre.auteur, livre.ISBN, ex_id or '-', etat))

    def _borrow_selected(self):
        if not self.current_user:
            messagebox.showwarning("Autorisaton", "Connectez-vous pour emprunter")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = item['values'][3]
        livre = self.biblio.emprunter_exemplaire(isbn, self.current_user)
        if livre is None:
            messagebox.showinfo("Indisponible", "Aucun exemplaire disponible ou réservation existante")
            return
        # persist both books and users
        try:
            BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
        except Exception as e:
            messagebox.showerror("Erreur", f"Echec sauvegarde transactionnelle: {e}")
        else:
            messagebox.showinfo("Ok", f"Livre emprunté: {livre.titre}")
            self._refresh_list()

    def _reserve_selected(self):
        if not self.current_user:
            messagebox.showwarning("Autorisaton", "Connectez-vous pour réserver")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = item['values'][3]
        ok = self.biblio.reserver_livre(isbn, user_obj=self.current_user, users_file=str(self.users_file))
        if ok:
            # persist both library and full users list
            try:
                BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
            except Exception:
                pass
            messagebox.showinfo("Réservé", "Réservation ajoutée")
        else:
            messagebox.showinfo("Réservation", "Vous avez déjà réservé ce livre ou réservation non autorisée")
        self._refresh_list()

    # ---------------- User actions ----------------
    def _refresh_user_panel(self):
        # loans
        self.lst_loans.delete(0, tk.END)
        self.lst_res.delete(0, tk.END)
        if not self.current_user:
            self.lbl_pen.config(text="0.00")
            return
        for l in self.current_user.loans:
            status = "en cours" if l.date_retour_effective is None else "rendu"
            self.lst_loans.insert(tk.END, f"{l.isbn} (ex:{l.exemplaire_id}) - {status} - due {l.date_retour_prevue}")
        for r in self.current_user.reservations:
            self.lst_res.insert(tk.END, f"{r.isbn} (ex:{r.exemplaire_id}) - {r.date_reservation}")
        self.lbl_pen.config(text=f"{self.current_user.penalites:.2f}")

    def _return_selected(self):
        sel = self.lst_loans.curselection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un prêt à rendre")
            return
        idx = sel[0]
        loan = self.current_user.loans[idx]
        montant = self.biblio.retourner_exemplaire(loan.exemplaire_id, self.current_user, str(self.users_file))
        try:
            BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
        except Exception:
            pass
        if montant:
            messagebox.showinfo("Retour", f"Retour enregistré. Pénalité: {montant:.2f} €")
        else:
            messagebox.showinfo("Retour", "Retour enregistré.")
        self._refresh_list()

    def _cancel_reservation(self):
        sel = self.lst_res.curselection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez une réservation")
            return
        idx = sel[0]
        res = self.current_user.reservations[idx]
        ok = self.biblio.annuler_reservation(res.isbn, user_obj=self.current_user, users_file=str(self.users_file))
        if ok:
            # ensure user reservation removed and persist full users list
            try:
                BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
            except Exception:
                pass
            messagebox.showinfo("Ok", "Réservation annulée")
        else:
            messagebox.showwarning("Erreur", "Impossible d'annuler")
        self._refresh_list()

    def _pay_penalties(self):
        if not self.current_user:
            return
        if self.current_user.penalites <= 0:
            messagebox.showinfo("Aucune pénalité", "Vous n'avez pas de pénalités à payer")
            return
        # simulate payment
        self.current_user.penalites = 0.0
        BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        messagebox.showinfo("Paiement", "Pénalités réglées")
        self._refresh_user_panel()

    # ---------------- Admin helpers ----------------
    def _admin_add_exemplar(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        dlg = tk.Toplevel(self)
        dlg.title("Ajouter exemplaire")
        ttk.Label(dlg, text="Titre:").grid(column=0, row=0, padx=6, pady=4)
        e_t = ttk.Entry(dlg); e_t.grid(column=1, row=0, padx=6)
        ttk.Label(dlg, text="Auteur:").grid(column=0, row=1, padx=6, pady=4)
        e_a = ttk.Entry(dlg); e_a.grid(column=1, row=1, padx=6)
        ttk.Label(dlg, text="ISBN:").grid(column=0, row=2, padx=6, pady=4)
        e_is = ttk.Entry(dlg); e_is.grid(column=1, row=2, padx=6)
        ttk.Label(dlg, text="Exemplaire ID:").grid(column=0, row=3, padx=6, pady=4)
        e_id = ttk.Entry(dlg); e_id.grid(column=1, row=3, padx=6)

        def do_add():
            t = e_t.get().strip(); a = e_a.get().strip(); i = e_is.get().strip(); ex = e_id.get().strip()
            if not (t and a and i and ex):
                messagebox.showwarning("Champs manquants", "Remplissez tous les champs")
                return
            self.biblio.ajouter_exemplaire(t, a, i, ex)
            try:
                self.biblio.sauvegarder(str(self.data_file))
            except Exception as e:
                messagebox.showerror("Erreur", f"Echec sauvegarde: {e}")
            dlg.destroy(); self._refresh_list()

        ttk.Button(dlg, text="Ajouter", command=do_add).grid(column=0, row=4, columnspan=2, pady=8)

    def _admin_delete_by_isbn(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        isbn = tk.simpledialog.askstring("Supprimer", "Entrez ISBN à supprimer:")
        if not isbn:
            return
        # remove all exemplaires with this ISBN
        removed = False
        for livre in list(self.biblio.livres):
            if livre.ISBN == isbn:
                self.biblio.livres.remove(livre)
                removed = True
        if removed:
            try:
                self.biblio.sauvegarder(str(self.data_file))
            except Exception:
                pass
            messagebox.showinfo("Ok", "Suppression effectuée")
            self._refresh_list()
        else:
            messagebox.showinfo("Info", "Aucun exemplaire trouvé pour cet ISBN")

    def _admin_mark_damaged(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        exid = tk.simpledialog.askstring("Marquer endommagé", "Entrez exemplaire ID:")
        if not exid:
            return
        found = False
        for livre in self.biblio.livres:
            if livre.exemplaire_id == exid:
                livre.etat = "endommage"
                found = True
                break
        if found:
            try:
                self.biblio.sauvegarder(str(self.data_file))
            except Exception:
                pass
            messagebox.showinfo("Ok", "Exemplaire marqué endommagé")
            self._refresh_list()
        else:
            messagebox.showinfo("Info", "Exemplaire non trouvé")

    def _admin_show_stats(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        # compute stats
        # popular books by loan history (use livre.history if available)
        loan_counts = {}
        for livre in self.biblio.livres:
            isbn = livre.ISBN
            hist = getattr(livre, 'history', []) or []
            loan_counts[isbn] = loan_counts.get(isbn, 0) + len(hist)
        # also add loans from users
        for u in self.users:
            for l in getattr(u, 'loans', []):
                loan_counts[l.isbn] = loan_counts.get(l.isbn, 0) + 0  # avoid double counting; we prefer livre.history

        # availability per ISBN
        availability = {}
        for livre in self.biblio.livres:
            isbn = livre.ISBN
            total, avail = availability.get(isbn, (0, 0))
            total += 1
            if getattr(livre, 'etat', 'disponible') == 'disponible':
                avail += 1
            availability[isbn] = (total, avail)

        # top popular
        popular = sorted(loan_counts.items(), key=lambda x: x[1], reverse=True)

        dlg = tk.Toplevel(self)
        dlg.title("Statistiques de la bibliothèque")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Livres les plus empruntés (ISBN: count)").pack(anchor=tk.W)
        txt = tk.Text(frm, height=6, width=80)
        txt.pack(fill=tk.X)
        for isbn, cnt in popular[:10]:
            # find title for isbn
            title = next((lv.titre for lv in self.biblio.livres if lv.ISBN == isbn), isbn)
            txt.insert(tk.END, f"{title} ({isbn}): {cnt}\n")

        ttk.Label(frm, text="Disponibilité par ISBN (available / total)").pack(anchor=tk.W, pady=(8, 0))
        txt2 = tk.Text(frm, height=8, width=80)
        txt2.pack(fill=tk.X)
        for isbn, (total, avail) in availability.items():
            txt2.insert(tk.END, f"{isbn}: {avail} / {total}\n")

        # active users
        active_users = [(u.username, sum(1 for l in getattr(u, 'loans', []) if l.date_retour_effective is None)) for u in self.users]
        active_sorted = sorted(active_users, key=lambda x: x[1], reverse=True)
        ttk.Label(frm, text="Utilisateurs actifs (en cours):").pack(anchor=tk.W, pady=(8, 0))
        txt3 = tk.Text(frm, height=6, width=80)
        txt3.pack(fill=tk.X)
        for uname, cnt in active_sorted[:20]:
            txt3.insert(tk.END, f"{uname}: {cnt}\n")

        ttk.Button(frm, text="Fermer", command=dlg.destroy).pack(pady=8)


def run_gui():
    app = BibliothequeApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
