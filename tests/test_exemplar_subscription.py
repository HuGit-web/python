from datetime import date, timedelta

from src.models import Bibliotheque
from src.users import User


def test_exemplar_status_and_counts():
    b = Bibliotheque("TestBiblio")
    b.ajouter_exemplaire("Titre1", "Auteur1", "ISBN-1", "ex1")
    b.ajouter_exemplaire("Titre1", "Auteur1", "ISBN-1", "ex2")

    stats = b.get_exemplar_statuses("ISBN-1")
    assert stats.get("disponible", 0) == 2

    assert b.set_exemplaire_status("ex2", "endommage") is True
    stats2 = b.get_exemplar_statuses("ISBN-1")
    assert stats2.get("disponible", 0) == 1
    assert stats2.get("endommage", 0) == 1

    ex = b.find_exemplar_by_id("ex1")
    assert ex is not None
    assert ex.exemplaire_id == "ex1"


def test_subscription_renew_and_can_borrow():
    u = User.create("tester", "pwd123", subscription_type="basique")
    u.subscription.date_expiration = date.today() - timedelta(days=1)
    assert u.subscription.date_expiration < date.today()
    assert u.can_borrow() is False

    new_exp = u.renew_subscription(30)
    assert new_exp == u.subscription.date_expiration
    assert u.subscription.date_expiration >= date.today()
    assert u.can_borrow() is True
