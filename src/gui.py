import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from typing import Optional

from .file_manager import BibliothequeAvecFichier
from .models import AggregatedLivre
from .users import User, SUBSCRIPTIONS
from .utils import get_data_dir


DATA_DIR = get_data_dir()
DATA_FILE = DATA_DIR / "bib.json"
USERS_FILE = DATA_DIR / "users.json"


class BibliothequeApp(tk.Tk):
    def __init__(self, data_file: Path = DATA_FILE, users_file: Path = USERS_FILE):
        super().__init__()
        self.title("Gestionnaire de bibliotheque")
        self.geometry("1200x700")
        self.resizable(True, True)

        self.data_file = data_file
        self.users_file = users_file
        # `get_data_dir()` already ensures the directory exists

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
        btn_logout = ttk.Button(top, text="Se déconnecter", command=self._logout)
        btn_logout.pack(side=tk.LEFT, padx=4)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned, width=340, padding=8)
        paned.add(left, weight=3)
        paned.add(right, weight=1)

        
        canvas = tk.Canvas(right)
        vsb = ttk.Scrollbar(right, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_inner = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=right_inner, anchor='nw')

        def _on_right_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_config(event, cid=window_id):
            try:
                canvas.itemconfig(cid, width=event.width)
            except Exception:
                pass

        right_inner.bind('<Configure>', _on_right_config)
        canvas.bind('<Configure>', _on_canvas_config)

        searchfrm = ttk.Frame(left)
        searchfrm.pack(fill=tk.X)
        ttk.Label(searchfrm, text="Rechercher par auteur:").pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(searchfrm, width=20)
        self.entry_search.pack(side=tk.LEFT, padx=6)
        ttk.Label(searchfrm, text="Titre:").pack(side=tk.LEFT)
        self.entry_title = ttk.Entry(searchfrm, width=20)
        self.entry_title.pack(side=tk.LEFT, padx=6)
        ttk.Label(searchfrm, text="Genre:").pack(side=tk.LEFT)
        self.combo_genre = ttk.Combobox(searchfrm, values=[], width=15)
        self.combo_genre.set("")
        self.combo_genre.pack(side=tk.LEFT, padx=6)
        ttk.Button(searchfrm, text="Rechercher", command=self._on_search).pack(side=tk.LEFT, padx=4)

        cols = ("#", "Titre", "Auteur", "Genre", "ISBN", "Exemplaire", "Etat", "Dispo/Total")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.pack(fill=tk.BOTH, expand=True)

        books_action_frame = ttk.Frame(left)
        books_action_frame.pack(fill=tk.X, pady=6)
        ttk.Button(books_action_frame, text="Emprunter le livre sélectionné", command=self._borrow_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(books_action_frame, text="Réserver le livre sélectionné", command=self._reserve_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(books_action_frame, text="Voir exemplaires", command=self._show_exemplars_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(books_action_frame, text="Historique du livre", command=self._show_book_history).pack(side=tk.LEFT, padx=4)
        ttk.Button(books_action_frame, text="Noter / Commenter", command=self._rate_comment_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(books_action_frame, text="Voir avis", command=self._show_reviews_selected).pack(side=tk.LEFT, padx=4)
        self.admin_frame = ttk.Frame(left)
        self.admin_frame.pack(fill=tk.X, pady=6)
        ttk.Button(self.admin_frame, text="Ajouter exemplaire", command=self._admin_add_exemplar).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Supprimer livre (ISBN)", command=self._admin_delete_by_isbn).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Marquer exemplaire endommagé", command=self._admin_mark_damaged).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Renouveler abonnement utilisateur", command=self._admin_renew_subscription).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Marquer pénalités payées", command=self._admin_mark_penalties_paid).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Modifier type d'abonnement", command=self._admin_change_subscription).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Modifier genre (ISBN)", command=self._admin_set_genre).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Modifier genre (sélection)", command=self._admin_set_genre_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(self.admin_frame, text="Stats bibliothèque", command=self._admin_show_stats).pack(side=tk.LEFT, padx=4)

        
        ttk.Label(right_inner, text="Utilisateur connecté:").pack(anchor=tk.W)
        self.lbl_user = ttk.Label(right_inner, text="(aucun)")
        self.lbl_user.pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(right_inner, text="Abonnement:").pack(anchor=tk.W)
        self.lbl_sub = ttk.Label(right_inner, text="(aucun)")
        self.lbl_sub.pack(anchor=tk.W, pady=(0, 8))
        # Show subscription limits (max emprunts, durée)
        self.lbl_limits = ttk.Label(right_inner, text="Limites: -")
        self.lbl_limits.pack(anchor=tk.W, pady=(0, 8))
        ttk.Button(right_inner, text="Recommandations", command=self._show_recommendations).pack(fill=tk.X, pady=4)

        ttk.Label(right_inner, text="Prêts en cours:").pack(anchor=tk.W)
        self.lst_loans = tk.Listbox(right_inner, height=8)
        self.lst_loans.pack(fill=tk.X)
        ttk.Button(right_inner, text="Rendre sélection", command=self._return_selected).pack(fill=tk.X, pady=4)

        ttk.Label(right_inner, text="Réservations:").pack(anchor=tk.W)
        self.lst_res = tk.Listbox(right_inner, height=6)
        self.lst_res.pack(fill=tk.X)
        ttk.Button(right_inner, text="Annuler réservation sélectionnée", command=self._cancel_reservation).pack(fill=tk.X, pady=4)

        ttk.Label(right_inner, text="Pénalités (€):").pack(anchor=tk.W)
        self.lbl_pen = ttk.Label(right_inner, text="0.00")
        self.lbl_pen.pack(anchor=tk.W)
        ttk.Button(right_inner, text="Payer pénalités", command=self._pay_penalties).pack(fill=tk.X, pady=6)
        ttk.Button(right_inner, text="Historique emprunts", command=self._show_history).pack(fill=tk.X, pady=4)
        ttk.Button(right_inner, text="Renouveler mon abonnement", command=self._renew_own_subscription).pack(fill=tk.X, pady=4)

    
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
        dlg.geometry("340x220")
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
        # Option to create an admin user at registration
        is_admin_var = tk.BooleanVar(value=False)
        chk_admin = ttk.Checkbutton(dlg, text="Administrateur", variable=is_admin_var)
        chk_admin.grid(column=0, row=3, columnspan=2, pady=(4, 6))

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
            # allow creating an admin account if checkbox checked
            new = User.create(uname, pwd, subscription_type=sub, is_admin=bool(is_admin_var.get()))
            self.users.append(new)
            BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
            messagebox.showinfo("Ok", "Compte créé. Connectez-vous.")
            dlg.destroy()

        ttk.Button(dlg, text="S'inscrire", command=do_register).grid(column=0, row=4, columnspan=2, pady=8)

    def _on_login(self):
        if not self.current_user:
            return
        self.lbl_user.config(text=self.current_user.username + (" (admin)" if self.current_user.is_admin else ""))
        
        if getattr(self.current_user, 'notifications', None):
            msgs = "\n".join(self.current_user.notifications)
            messagebox.showinfo("Notifications", msgs)
            
            self.current_user.notifications.clear()
            BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        self._refresh_user_panel()
        
        if self.current_user and self.current_user.is_admin:
            self.admin_frame.pack(fill=tk.X, pady=6)
        else:
            self.admin_frame.forget()

    def _logout(self):
        self.current_user = None
        self.lbl_user.config(text="(aucun)")
        self.lbl_sub.config(text="(aucun)")
        try:
            self.admin_frame.forget()
        except Exception:
            pass
        self._refresh_list()

    
    def _on_search(self):
        auteur = self.entry_search.get().strip()
        titre = getattr(self, 'entry_title', None) and self.entry_title.get().strip()
        genre = getattr(self, 'combo_genre', None) and (self.combo_genre.get() or '').strip()
        if not auteur and not titre:
            self._refresh_list()
            return
        if titre:
            resultats = [lv for lv in self.biblio.lister() if titre.lower() in getattr(lv, 'titre', '').lower()]
        else:
            resultats = self.biblio.recherche_par_auteur(auteur)
        if genre:
            resultats = [lv for lv in resultats if getattr(lv, 'genre', None) and genre.lower() in getattr(lv, 'genre', '').lower()]
        self._populate_tree(resultats)

    def _refresh_list(self):
        self._populate_tree(self.biblio.lister())
        self._refresh_user_panel()

    def _populate_tree(self, livres):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        try:
            genres = sorted({getattr(lv, 'genre') for lv in self.biblio.lister() if getattr(lv, 'genre', None)})
            if hasattr(self, 'combo_genre'):
                self.combo_genre['values'] = [''] + genres
        except Exception:
            pass

        
        by_isbn: dict = {}
        for lv in livres:
            by_isbn.setdefault(lv.ISBN, []).append(lv)

        for idx, (isbn, lv_list) in enumerate(by_isbn.items(), start=1):
            rep = lv_list[0]
            titre = getattr(rep, 'titre', '')
            auteur = getattr(rep, 'auteur', '')
            genre = getattr(rep, 'genre', '')
            
            
            try:
                exmap = getattr(self.biblio, 'exemplaires', None)
                if isinstance(exmap, dict) and isbn in exmap:
                    entry = exmap[isbn]
                    total = int(entry.get('total', 0))
                    avail = int(entry.get('disponibles', 0))
                else:
                        stats = self.biblio.get_exemplar_statuses(isbn)
                        total = int(stats.get('total', 0))
                        avail = int(stats.get('disponible', 0))
            except Exception:
                        
                        total = len(lv_list)
                        avail = 0
                        for l in lv_list:
                            try:
                                avail += int(getattr(l, 'disponibles', 1)) if hasattr(l, 'nb_exemplaire') else (1 if getattr(l, 'etat', 'disponible') == 'disponible' else 0)
                            except Exception:
                                avail += 0
            dispo_txt = f"{avail}/{total}"
            
            if avail == 0:
                etat = 'indisponible'
            elif avail == total:
                etat = 'disponible'
            else:
                etat = 'partiellement disponible'
            
            ex_id = '-'
            self.tree.insert("", tk.END, values=(idx, titre, auteur, genre, isbn, ex_id, etat, dispo_txt))

    def _borrow_selected(self):
        if not self.current_user:
            messagebox.showwarning("Autorisaton", "Connectez-vous pour emprunter")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = str(item['values'][4]).strip()
        try:
            livre = self.biblio.emprunter_exemplaire(isbn, self.current_user)
        except ValueError as e:
            
            messagebox.showinfo("Indisponible", str(e))
            return
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'emprunt: {e}")
            return

        try:
            BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
        except Exception as e:
            messagebox.showerror("Erreur", f"Echec sauvegarde transactionnelle: {e}")
            
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
        isbn = str(item['values'][4]).strip()
        ok = self.biblio.reserver_livre(isbn, user_obj=self.current_user, users_file=str(self.users_file))
        if ok:
            
            try:
                BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
            except Exception:
                pass
            messagebox.showinfo("Réservé", "Réservation ajoutée")
        else:
            messagebox.showinfo("Réservation", "Vous avez déjà réservé ce livre ou réservation non autorisée")
        self._refresh_list()

    
    def _refresh_user_panel(self):
        
        self.lst_loans.delete(0, tk.END)
        self.lst_res.delete(0, tk.END)
        if not self.current_user:
            self.lbl_pen.config(text="0.00")
            self.lbl_sub.config(text="(aucun)")
            try:
                self.lbl_limits.config(text="Limites: -")
            except Exception:
                pass
            # ensure active loans mapping exists
            self._active_loans = []
            return
        # Only show active loans (not yet returned) in the "Prêts en cours" list
        self._active_loans = [l for l in getattr(self.current_user, 'loans', []) if getattr(l, 'date_retour_effective', None) is None]
        for l in self._active_loans:
            status = "en cours"
            self.lst_loans.insert(tk.END, f"{l.isbn} (ex:{l.exemplaire_id}) - {status} - due {l.date_retour_prevue}")
        for r in self.current_user.reservations:
            self.lst_res.insert(tk.END, f"{r.isbn} (ex:{r.exemplaire_id}) - {r.date_reservation}")
        self.lbl_pen.config(text=f"{self.current_user.penalites:.2f}")
        
        if getattr(self.current_user, 'subscription', None):
            sub = self.current_user.subscription
            self.lbl_sub.config(text=f"{sub.type} — expire le {sub.date_expiration}")
            try:
                # ensure monthly reset logic runs (will reset monthly_emprunts when month changed)
                try:
                    _ = self.current_user.can_borrow()
                except Exception:
                    pass
                info = SUBSCRIPTIONS.get(sub.type, {})
                monthly_limit = info.get('monthly_limit', None)
                duree = info.get('duree_jours', '?')
                current = int(getattr(self.current_user, 'monthly_emprunts', 0) or 0)
                if monthly_limit is None:
                    limits_txt = f"Limites: Illimité, durée {duree} jours — Emprunts ce mois: {current}"
                else:
                    limits_txt = f"Limites: Emprunts ce mois: {current}/{int(monthly_limit)} , durée {duree} jours"
                self.lbl_limits.config(text=limits_txt)
            except Exception:
                try:
                    self.lbl_limits.config(text="Limites: -")
                except Exception:
                    pass
        else:
            self.lbl_sub.config(text="(aucun)")
            try:
                self.lbl_limits.config(text="Limites: -")
            except Exception:
                pass

    def _show_recommendations(self):
        if not self.current_user:
            messagebox.showwarning("Accès", "Connectez-vous pour voir des recommandations")
            return
        recs = self.biblio.recommend_for_user(self.current_user, limit=10)
        dlg = tk.Toplevel(self)
        dlg.title("Recommandations")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        if not recs:
            ttk.Label(frm, text="Aucune recommandation disponible pour l'instant.").pack()
        else:
            tree = ttk.Treeview(frm, columns=("Titre", "Auteur", "ISBN", "Etat"), show="headings")
            for c in ("Titre", "Auteur", "ISBN", "Etat"):
                tree.heading(c, text=c)
            tree.pack(fill=tk.BOTH, expand=True)
            for lv in recs:
                state = 'disponible' if getattr(lv, 'disponibles', 0) > 0 else 'indisponible'
                tree.insert("", tk.END, values=(getattr(lv, 'titre', ''), getattr(lv, 'auteur', ''), getattr(lv, 'ISBN', ''), state))
        ttk.Button(frm, text="Fermer", command=dlg.destroy).pack(pady=8)

    def _return_selected(self):
        sel = self.lst_loans.curselection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un prêt à rendre")
            return
        idx = sel[0]
        # Map selection index to the active loans list
        try:
            loan = self._active_loans[idx]
        except Exception:
            messagebox.showerror("Erreur", "Prêt sélectionné invalide")
            return
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
        
        self.current_user.penalites = 0.0
        BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        messagebox.showinfo("Paiement", "Pénalités réglées")
        self._refresh_user_panel()

    def _show_history(self):
        if not self.current_user:
            messagebox.showwarning("Accès", "Connectez-vous pour voir l'historique")
            return
        dlg = tk.Toplevel(self)
        dlg.title(f"Historique de {self.current_user.username}")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        cols = ("ISBN", "Ex.", "Emprunt", "Prévu", "Retour", "Pénalité")
        tree = ttk.Treeview(frm, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill=tk.BOTH, expand=True)

        for l in self.current_user.loans:
            date_emp = l.date_emprunt.isoformat() if getattr(l, 'date_emprunt', None) else ''
            date_prev = l.date_retour_prevue.isoformat() if getattr(l, 'date_retour_prevue', None) else ''
            date_ret = l.date_retour_effective.isoformat() if getattr(l, 'date_retour_effective', None) else ''
            pen = f"{getattr(l, 'penalite_acquise', 0.0):.2f}"
            tree.insert("", tk.END, values=(l.isbn, l.exemplaire_id or '-', date_emp, date_prev, date_ret, pen))

        ttk.Button(frm, text="Fermer", command=dlg.destroy).pack(pady=6)

    
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
        ttk.Label(dlg, text="Genre:").grid(column=0, row=3, padx=6, pady=4)
        e_gen = ttk.Entry(dlg); e_gen.grid(column=1, row=3, padx=6)
        ttk.Label(dlg, text="Exemplaire ID:").grid(column=0, row=4, padx=6, pady=4)
        e_id = ttk.Entry(dlg); e_id.grid(column=1, row=4, padx=6)

        def do_add():
            t = e_t.get().strip(); a = e_a.get().strip(); i = e_is.get().strip(); gen = e_gen.get().strip(); ex = e_id.get().strip()
            if not (t and a and i and ex):
                messagebox.showwarning("Champs manquants", "Remplissez tous les champs")
                return
            # try to pass genre to ajouter_exemplaire; fall back if signature doesn't accept it
            try:
                self.biblio.ajouter_exemplaire(t, a, i, ex, genre=gen if gen else None)
            except TypeError:
                self.biblio.ajouter_exemplaire(t, a, i, ex)
            try:
                self.biblio.sauvegarder(str(self.data_file))
            except Exception as e:
                messagebox.showerror("Erreur", f"Echec sauvegarde: {e}")
            dlg.destroy(); self._refresh_list()

        # place the Add button on the dialog (row adjusted for new Genre field)
        ttk.Button(dlg, text="Ajouter", command=do_add).grid(column=0, row=5, columnspan=2, pady=8)

    def _admin_delete_by_isbn(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        isbn = simpledialog.askstring("Supprimer", "Entrez ISBN à supprimer:")
        if not isbn:
            return
        isbn = isbn.strip()
        if not isbn:
            return

        removed = False
        for livre in list(self.biblio.livres):
            if str(getattr(livre, 'ISBN', '')).strip() == isbn:
                self.biblio.livres.remove(livre)
                removed = True
        if removed:
            try:
                
                BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
            except Exception:
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
        exid = simpledialog.askstring("Marquer endommagé", "Entrez exemplaire ID:")
        if not exid:
            return
        found = False
        for livre in self.biblio.livres:
            for d in getattr(livre, 'exemplaires_details', []):
                if d.get('exemplaire_id') == exid:
                    d['etat'] = 'endommage'
                    
                    if d.get('etat') != 'disponible':
                        try:
                            livre.disponibles = max(0, livre.disponibles - 1)
                        except Exception:
                            pass
                    found = True
                    break
            if found:
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

    def _admin_renew_subscription(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        uname = simpledialog.askstring("Renouveler", "Nom d'utilisateur à renouveler:")
        if not uname:
            return
        days = simpledialog.askinteger("Jours", "Nombre de jours à ajouter:", minvalue=1, initialvalue=365)
        if not days:
            return
        target = next((u for u in self.users if u.username == uname), None)
        if not target:
            messagebox.showinfo("Introuvable", "Utilisateur non trouvé")
            return
        new_exp = target.renew_subscription(days)
        BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        messagebox.showinfo("Renouvelé", f"Abonnement de {uname} prolongé jusqu'à {new_exp}")

    def _admin_change_subscription(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        uname = simpledialog.askstring("Changer abonnement", "Nom d'utilisateur:")
        if not uname:
            return
        target = next((u for u in self.users if u.username == uname), None)
        if not target:
            messagebox.showinfo("Introuvable", "Utilisateur non trouvé")
            return
        new_type = simpledialog.askstring("Type", "Nouveau type (basique/premium/VIP):")
        if not new_type:
            return
        try:
            from datetime import date, timedelta
            from .users import SUBSCRIPTIONS, Subscription
            info = SUBSCRIPTIONS.get(new_type, SUBSCRIPTIONS['basique'])
            duration = info.get('duree_jours', 14)
            if not target.subscription:
                target.subscription = Subscription(new_type, date.today(), date.today() + timedelta(days=duration * 12))
            else:
                target.subscription.type = new_type
                target.subscription.date_debut = date.today()
                target.subscription.date_expiration = date.today() + timedelta(days=duration * 12)
            BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
            messagebox.showinfo("Ok", f"Abonnement de {uname} changé en {new_type}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier l'abonnement: {e}")

    def _admin_set_genre(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        isbn = simpledialog.askstring("Modifier genre", "Entrez ISBN:")
        if not isbn:
            return
        isbn = isbn.strip()
        new_genre = simpledialog.askstring("Genre", "Entrez genre (ex: Science-fiction):")
        if new_genre is None:
            return
        new_genre = new_genre.strip()
        updated = False
        for livre in self.biblio.livres:
            if str(getattr(livre, 'ISBN', '')).strip() == isbn:
                try:
                    livre.genre = new_genre
                except Exception:
                    pass
                updated = True
        if not updated:
            messagebox.showinfo("Introuvable", "Aucun livre trouvé pour cet ISBN")
            return
        try:
            BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
        except Exception:
            try:
                self.biblio.sauvegarder(str(self.data_file))
            except Exception:
                pass
        messagebox.showinfo("Ok", f"Genre mis à jour pour ISBN {isbn}")
        self._refresh_list()

    def _admin_set_genre_selected(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre dans la liste")
            return
        item = self.tree.item(sel[0])
        try:
            isbn = str(item['values'][4]).strip()
        except Exception:
            messagebox.showerror("Erreur", "Impossible de lire l'ISBN de la sélection")
            return
        new_genre = simpledialog.askstring("Genre", "Entrez nouveau genre:")
        if new_genre is None:
            return
        new_genre = new_genre.strip()
        updated = False
        for livre in self.biblio.livres:
            if str(getattr(livre, 'ISBN', '')).strip() == isbn:
                try:
                    livre.genre = new_genre
                except Exception:
                    pass
                updated = True
        if not updated:
            messagebox.showinfo("Introuvable", "Aucun livre trouvé pour cet ISBN")
            return
        try:
            BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
        except Exception:
            try:
                self.biblio.sauvegarder(str(self.data_file))
            except Exception:
                pass
        messagebox.showinfo("Ok", f"Genre mis à jour pour ISBN {isbn}")
        self._refresh_list()

    def _admin_trim_exemplars(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        maxn = simpledialog.askinteger("Max exemplaires", "Nombre maximum d'exemplaires par ISBN:", minvalue=1, initialvalue=5)
        if not maxn:
            return
        removed = 0
        try:
            removed = self.biblio.trim_exemplaires(maxn)
            if removed:
                
                try:
                    self.biblio.sauvegarder(str(self.data_file))
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer exemplaires: {e}")
            return
        messagebox.showinfo("Terminé", f"Exemplaires supprimés: {removed}")
        self._refresh_list()

    def _show_exemplars_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = str(item['values'][4]).strip()
        exs = self.biblio.trouver_exemplaires(isbn)
        dlg = tk.Toplevel(self)
        dlg.title(f"Exemplaires de {isbn}")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frm, columns=("id", "etat", "titre"), show="headings")
        for c in ("id", "etat", "titre"):
            tree.heading(c, text=c)
        tree.pack(fill=tk.BOTH, expand=True)
        for lv in exs:
            
            details = getattr(lv, 'exemplaires_details', None) or []
            if details:
                for d in details:
                    tree.insert("", tk.END, values=(d.get('exemplaire_id', '-'), d.get('etat', 'disponible'), getattr(lv, 'titre', '')))
            else:
                
                total = int(getattr(lv, 'nb_exemplaire', 0) or 0)
                dispo = int(getattr(lv, 'disponibles', 0) or 0)
                for i in range(total):
                    eid = f"{getattr(lv,'ISBN','unknown')}-synth{i+1}"
                    state = 'disponible' if i < dispo else 'emprunte'
                    tree.insert("", tk.END, values=(eid, state, getattr(lv, 'titre', '')))

        def change_status():
            if not self.current_user or not self.current_user.is_admin:
                messagebox.showwarning("Accès refusé", "Administrateur requis")
                return
            sel2 = tree.selection()
            if not sel2:
                messagebox.showwarning("Sélection", "Sélectionnez un exemplaire")
                return
            vals = tree.item(sel2[0])['values']
            exid = vals[0]
            new = simpledialog.askstring("Nouveau statut", "Entrez nouveau statut (disponible/emprunte/endommage/perdu):")
            if not new:
                return
            ok = self.biblio.set_exemplaire_status(exid, new)
            if ok:
                try:
                    self.biblio.sauvegarder(str(self.data_file))
                except Exception:
                    pass
                messagebox.showinfo("Ok", "Statut modifié")
                dlg.destroy()
                self._refresh_list()
            else:
                messagebox.showerror("Erreur", "Impossible de modifier statut")

        btnf = ttk.Frame(frm)
        btnf.pack(fill=tk.X, pady=6)
        ttk.Button(btnf, text="Changer statut (admin)", command=change_status).pack(side=tk.LEFT, padx=4)
        ttk.Button(btnf, text="Fermer", command=dlg.destroy).pack(side=tk.RIGHT, padx=4)

    def _show_book_history(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = str(item['values'][4]).strip()
        
        entries = []
        for lv in self.biblio.trouver_exemplaires(isbn):
            for h in getattr(lv, 'history', []):
                entries.append(h)
        dlg = tk.Toplevel(self)
        dlg.title(f"Historique livre {isbn}")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        cols = ("username", "isbn", "exemplaire_id", "date_emprunt", "date_retour_prevue", "date_retour_effective")
        tree = ttk.Treeview(frm, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill=tk.BOTH, expand=True)
        for e in entries:
            tree.insert("", tk.END, values=(e.get('username'), e.get('isbn'), e.get('exemplaire_id'), e.get('date_emprunt'), e.get('date_retour_prevue'), e.get('date_retour_effective')))
        ttk.Button(frm, text="Fermer", command=dlg.destroy).pack(pady=8)

    def _rate_comment_selected(self):
        if not self.current_user:
            messagebox.showwarning("Accès", "Connectez-vous pour noter/commenter")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = str(item['values'][4]).strip()
        dlg = tk.Toplevel(self)
        dlg.title("Noter et commenter")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Note (1-5):").pack(anchor=tk.W)
        spin = tk.Spinbox(frm, from_=1, to=5, width=5)
        spin.pack(anchor=tk.W)
        ttk.Label(frm, text="Commentaire:").pack(anchor=tk.W, pady=(8,0))
        txt = tk.Text(frm, height=6, width=60)
        txt.pack(fill=tk.BOTH, expand=True)

        def do_send():
            try:
                rating = int(spin.get())
            except Exception:
                messagebox.showwarning("Note invalide", "Entrez une note entre 1 et 5")
                return
            comment = txt.get("1.0", tk.END).strip()
            ok = self.biblio.add_review(isbn, self.current_user.username, rating, comment)
            if ok:
                try:
                    BibliothequeAvecFichier.sauvegarder_transactionnel(self.biblio, self.users, str(self.data_file), str(self.users_file))
                except Exception:
                    pass
                messagebox.showinfo("Merci", "Avis enregistré")
                dlg.destroy()
            else:
                messagebox.showerror("Erreur", "Impossible d'enregistrer l'avis")

        ttk.Button(frm, text="Envoyer", command=do_send).pack(pady=8)

    def _show_reviews_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un livre")
            return
        item = self.tree.item(sel[0])
        isbn = str(item['values'][4]).strip()
        
        reviews = []
        for lv in self.biblio.trouver_exemplaires(isbn):
            for r in getattr(lv, 'reviews', []):
                reviews.append(r)
        dlg = tk.Toplevel(self)
        dlg.title(f"Avis pour {isbn}")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        if not reviews:
            ttk.Label(frm, text="Aucun avis pour ce livre").pack()
        else:
            tree = ttk.Treeview(frm, columns=("user", "rating", "comment"), show="headings")
            for c in ("user", "rating", "comment"):
                tree.heading(c, text=c)
            tree.pack(fill=tk.BOTH, expand=True)
            for r in reviews:
                tree.insert("", tk.END, values=(r.get('username'), r.get('rating'), (r.get('comment') or '')[:200]))
        ttk.Button(frm, text="Fermer", command=dlg.destroy).pack(pady=8)

    def _admin_mark_penalties_paid(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        uname = tk.simpledialog.askstring("Marquer payé", "Nom d'utilisateur:")
        if not uname:
            return
        target = next((u for u in self.users if u.username == uname), None)
        if not target:
            messagebox.showinfo("Introuvable", "Utilisateur non trouvé")
            return
        target.penalites = 0.0
        BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        messagebox.showinfo("Ok", f"Pénalités de {uname} marquées payées")

    def _renew_own_subscription(self):
        if not self.current_user:
            messagebox.showwarning("Accès", "Connectez-vous")
            return
        days = tk.simpledialog.askinteger("Renouveler", "Nombre de jours à ajouter:", minvalue=1, initialvalue=365)
        if not days:
            return
        new_exp = self.current_user.renew_subscription(days)
        BibliothequeAvecFichier.sauvegarder_users(self.users, str(self.users_file))
        messagebox.showinfo("Renouvelé", f"Votre abonnement est prolongé jusqu'à {new_exp}")

    def _admin_show_stats(self):
        if not self.current_user or not self.current_user.is_admin:
            messagebox.showwarning("Accès refusé", "Administrateur requis")
            return
        stats = self.biblio.stats(self.users)
        dlg = tk.Toplevel(self)
        dlg.title("Statistiques de la bibliothèque")
        frm = ttk.Frame(dlg, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Livres les plus empruntés (ISBN - Titre: count)").pack(anchor=tk.W)
        txt = tk.Text(frm, height=6, width=80)
        txt.pack(fill=tk.X)
        for isbn, title, cnt in stats.get('popular_books', [])[:10]:
            txt.insert(tk.END, f"{title} ({isbn}): {cnt}\n")

        ttk.Label(frm, text="Nombre d'exemplaires par ISBN").pack(anchor=tk.W, pady=(8, 0))
        txt2 = tk.Text(frm, height=6, width=80)
        txt2.pack(fill=tk.X)
        for isbn, cnt in stats.get('multi_exemplaires', {}).items():
            txt2.insert(tk.END, f"{isbn}: {cnt} exemplaires\n")

        ttk.Label(frm, text="Statut des exemplaires (compteurs)").pack(anchor=tk.W, pady=(8, 0))
        txt4 = tk.Text(frm, height=6, width=80)
        txt4.pack(fill=tk.X)
        for st, cnt in stats.get('exemplar_status_counts', {}).items():
            txt4.insert(tk.END, f"{st}: {cnt}\n")

        ttk.Label(frm, text="Utilisateurs actifs / prêts en retard").pack(anchor=tk.W, pady=(8, 0))
        txt3 = tk.Text(frm, height=4, width=80)
        txt3.pack(fill=tk.X)
        txt3.insert(tk.END, f"Utilisateurs actifs: {stats.get('active_users', 0)}\n")
        txt3.insert(tk.END, f"Prêts en retard: {stats.get('overdue_loans', 0)}\n")

        ttk.Button(frm, text="Fermer", command=dlg.destroy).pack(pady=8)


def run_gui():
    app = BibliothequeApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
