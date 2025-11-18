import json
from src.models import Livre, LivreNumerique, Bibliotheque

def test_livre_to_dict():
    l = Livre("Titre", "Auteur", "ISBN1")
    d = l.to_dict()
    assert d["type"] == "Livre"
    assert d["titre"] == "Titre"

def test_livre_numerique_to_dict():
    ln = LivreNumerique("T", "A", "ISBN2", "5MB")
    d = ln.to_dict()
    assert d["type"] == "Livre Numerique"
    assert d["taille_fichier"] == "5MB"

def test_bibliotheque_crud(tmp_path):
    b = Bibliotheque("Test")
    l1 = Livre("T1", "A1", "I1")
    l2 = LivreNumerique("T2", "A2", "I2", "1MB")
    b.ajouter_livre(l1)
    b.ajouter_livre(l2)
    assert len(b.livres) == 2
    assert b.supprimer_livre("I1") is True
    assert len(b.livres) == 1
    # save and load
    p = tmp_path / "biblio.json"
    b.sauvegarder(str(p))
    b2 = Bibliotheque("Reloaded")
    b2.charger(str(p))
    assert any(l.ISBN == "I2" for l in b2.livres)
