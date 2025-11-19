import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from .file_manager import BibliothequeAvecFichier
from .models import Livre


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "bib.json"


class BibliothequeApp(tk.Tk):
    def __init__(self, data_file: Path = DATA_FILE):
        super().__init__()
        self.title("Gestionnaire de bibliotheque")
        self.geometry("800x520")
        self.resizable(False, False)

        self.data_file = data_file
        self.biblio = BibliothequeAvecFichier("Mes livres")
        # try loading existing data silently
        try:
            if self.data_file.exists():
                self.biblio.charger(str(self.data_file))
        except Exception:
            # ignore load errors at startup
            pass

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Top frame: form to add a book
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.X)

        ttk.Label(frm, text="Titre:").grid(column=0, row=0, sticky=tk.W, padx=4, pady=4)
        self.entry_titre = ttk.Entry(frm, width=40)
        self.entry_titre.grid(column=1, row=0, sticky=tk.W, padx=4)

        ttk.Label(frm, text="Auteur:").grid(column=0, row=1, sticky=tk.W, padx=4, pady=4)
        self.entry_auteur = ttk.Entry(frm, width=40)
        self.entry_auteur.grid(column=1, row=1, sticky=tk.W, padx=4)

        ttk.Label(frm, text="ISBN:").grid(column=0, row=2, sticky=tk.W, padx=4, pady=4)
        self.entry_isbn = ttk.Entry(frm, width=40)
        self.entry_isbn.grid(column=1, row=2, sticky=tk.W, padx=4)

        btn_add = ttk.Button(frm, text="Ajouter le livre", command=self._on_add)
        btn_add.grid(column=2, row=0, rowspan=3, padx=8)

        # Search frame
        frm2 = ttk.Frame(self, padding=(10, 4))
        frm2.pack(fill=tk.X)
        ttk.Label(frm2, text="Rechercher par auteur:").grid(column=0, row=0, sticky=tk.W)
        self.entry_search = ttk.Entry(frm2, width=40)
        self.entry_search.grid(column=1, row=0, sticky=tk.W, padx=6)
        btn_search = ttk.Button(frm2, text="Rechercher", command=self._on_search)
        btn_search.grid(column=2, row=0, padx=6)
        btn_show_all = ttk.Button(frm2, text="Afficher tout", command=self._refresh_list)
        btn_show_all.grid(column=3, row=0, padx=6)

        # List / display area
        cols = ("#", "Titre", "Auteur", "ISBN")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("#", width=40, anchor=tk.CENTER)
        self.tree.column("Titre", width=360)
        self.tree.column("Auteur", width=220)
        self.tree.column("ISBN", width=160)
        self.tree.pack(fill=tk.BOTH, padx=10, pady=10)

    def _on_add(self):
        titre = self.entry_titre.get().strip()
        auteur = self.entry_auteur.get().strip()
        isbn = self.entry_isbn.get().strip()
        if not titre or not auteur or not isbn:
            messagebox.showwarning("Champs manquants", "Veuillez renseigner titre, auteur et ISBN.")
            return

        livre = Livre(titre, auteur, isbn)
        self.biblio.ajouter_livre(livre)
        try:
            self.biblio.sauvegarder(str(self.data_file))
        except Exception as e:
            messagebox.showerror("Erreur sauvegarde", f"Echec sauvegarde: {e}")
        else:
            self._clear_form()
            self._refresh_list()

    def _on_search(self):
        auteur = self.entry_search.get().strip()
        if not auteur:
            self._refresh_list()
            return
        resultats = self.biblio.recherche_par_auteur(auteur)
        self._populate_tree(resultats)

    def _clear_form(self):
        self.entry_titre.delete(0, tk.END)
        self.entry_auteur.delete(0, tk.END)
        self.entry_isbn.delete(0, tk.END)

    def _refresh_list(self):
        self._populate_tree(self.biblio.lister())

    def _populate_tree(self, livres):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, livre in enumerate(livres, start=1):
            self.tree.insert("", tk.END, values=(idx, livre.titre, livre.auteur, livre.ISBN))


def run_gui():
    app = BibliothequeApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
