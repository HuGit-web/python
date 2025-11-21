from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, date
from typing import List, Optional
import hashlib


SUBSCRIPTIONS = {
    "basique": {"max_emprunts": 1, "duree_jours": 14, "penalite_par_jour": 0.5},
    "premium": {"max_emprunts": 3, "duree_jours": 21, "penalite_par_jour": 0.5},
    "VIP": {"max_emprunts": 10, "duree_jours": 28, "penalite_par_jour": 0.3},
}


def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


@dataclass
class Loan:
    isbn: str
    exemplaire_id: Optional[str]
    date_emprunt: date
    date_retour_prevue: date
    date_retour_effective: Optional[date] = None
    penalite_acquise: float = 0.0

    def to_dict(self):
        d = asdict(self)
        d["date_emprunt"] = self.date_emprunt.isoformat()
        d["date_retour_prevue"] = self.date_retour_prevue.isoformat()
        d["date_retour_effective"] = self.date_retour_effective.isoformat() if self.date_retour_effective else None
        return d


@dataclass
class Reservation:
    isbn: str
    exemplaire_id: Optional[str]
    date_reservation: date

    def to_dict(self):
        d = asdict(self)
        d["date_reservation"] = self.date_reservation.isoformat()
        return d


@dataclass
class Subscription:
    type: str
    date_debut: date
    date_expiration: date

    def to_dict(self):
        d = asdict(self)
        d["date_debut"] = self.date_debut.isoformat()
        d["date_expiration"] = self.date_expiration.isoformat()
        return d
    
    def renew(self, extra_days: int):
        self.date_expiration = self.date_expiration + timedelta(days=extra_days)


@dataclass
class User:
    username: str
    _pwd_hash: str
    is_admin: bool = False
    subscription: Subscription | None = None
    loans: List[Loan] = field(default_factory=list)
    reservations: List[Reservation] = field(default_factory=list)
    penalites: float = 0.0
    notifications: List[str] = field(default_factory=list)
    monthly_emprunts: int = 0
    last_reset: Optional[date] = None

    @classmethod
    def create(cls, username: str, password: str, subscription_type: str = "basique", is_admin: bool = False) -> "User":
        now = date.today()
        sub_info = SUBSCRIPTIONS.get(subscription_type, SUBSCRIPTIONS["basique"])
        duration = sub_info.get("duree_jours", 14)
        sub = Subscription(subscription_type, now, now + timedelta(days=duration * 12))
        return cls(username, hash_password(password), is_admin=is_admin, subscription=sub)

    def check_password(self, password: str) -> bool:
        return self._pwd_hash == hash_password(password)

    def can_borrow(self) -> bool:
        if self.penalites > 0:
            return False
        if not self.subscription:
            return False
        
        today = date.today()
        if self.subscription.date_expiration < today:
            return False
        today = date.today()
        if self.last_reset is None or (self.last_reset.year, self.last_reset.month) != (today.year, today.month):
            self.monthly_emprunts = 0
            self.last_reset = today.replace(day=1)

        sub_info = SUBSCRIPTIONS.get(self.subscription.type, SUBSCRIPTIONS["basique"])
        max_emprunts = sub_info["max_emprunts"]
        active = sum(1 for l in self.loans if l.date_retour_effective is None)

        if active >= max_emprunts:
            return False

        return self.monthly_emprunts < max_emprunts

    def renew_subscription(self, extra_days: int) -> date | None:
        
        if not self.subscription:
            return None
        self.subscription.renew(extra_days)
        return self.subscription.date_expiration

    def borrow(self, isbn: str, exemplaire_id: Optional[str] = None) -> Loan:
        if not self.can_borrow():
            raise ValueError("Emprunt non autorise: limites ou penalites")
        sub_info = SUBSCRIPTIONS.get(self.subscription.type, SUBSCRIPTIONS["basique"])
        duree = sub_info["duree_jours"]
        now = date.today()
        loan = Loan(isbn, exemplaire_id, now, now + timedelta(days=duree))
        self.loans.append(loan)
        self.monthly_emprunts += 1
        return loan

    def return_loan(self, loan: Loan) -> float:
        if loan.date_retour_effective is not None:
            return 0.0
        now = date.today()
        loan.date_retour_effective = now
        if now > loan.date_retour_prevue:
            jours_retard = (now - loan.date_retour_prevue).days
            sub_info = SUBSCRIPTIONS.get(self.subscription.type, SUBSCRIPTIONS["basique"])
            montant = jours_retard * sub_info.get("penalite_par_jour", 0.5)
            loan.penalite_acquise = montant
            self.penalites += montant
            return montant
        return 0.0

    def reserve(self, isbn: str, exemplaire_id: Optional[str] = None) -> Reservation:
        r = Reservation(isbn, exemplaire_id, date.today())
        self.reservations.append(r)
        return r

    def to_dict(self):
        return {
            "username": self.username,
            "_pwd_hash": self._pwd_hash,
            "is_admin": self.is_admin,
            "subscription": self.subscription.to_dict() if self.subscription else None,
            "loans": [l.to_dict() for l in self.loans],
            "reservations": [r.to_dict() for r in self.reservations],
            "penalites": self.penalites,
            "notifications": list(self.notifications),
            "monthly_emprunts": self.monthly_emprunts,
            "last_reset": self.last_reset.isoformat() if self.last_reset else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        sub = None
        if data.get("subscription"):
            sd = data["subscription"]
            sub = Subscription(sd["type"], date.fromisoformat(sd["date_debut"]), date.fromisoformat(sd["date_expiration"]))
        user = cls(data["username"], data.get("_pwd_hash", ""), is_admin=data.get("is_admin", False), subscription=sub)
        for l in data.get("loans", []):
            loan = Loan(l["isbn"], l.get("exemplaire_id"), date.fromisoformat(l["date_emprunt"]), date.fromisoformat(l["date_retour_prevue"]))
            if l.get("date_retour_effective"):
                loan.date_retour_effective = date.fromisoformat(l["date_retour_effective"])
            loan.penalite_acquise = l.get("penalite_acquise", 0.0)
            user.loans.append(loan)
        for r in data.get("reservations", []):
            res = Reservation(r["isbn"], r.get("exemplaire_id"), date.fromisoformat(r["date_reservation"]))
            user.reservations.append(res)
        user.penalites = data.get("penalites", 0.0)
        user.notifications = data.get("notifications", [])
        user.monthly_emprunts = data.get("monthly_emprunts", 0)
        if data.get("last_reset"):
            user.last_reset = date.fromisoformat(data.get("last_reset"))
        return user
