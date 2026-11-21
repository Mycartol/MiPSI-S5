
from app import app
from extensions import db
from models import Uzytkownik, Rola


with app.app_context():
    email = input("Podaj e-mail użytkownika: ").strip().lower()
    nazwa_roli = input(
        "Podaj rolę (admin / obsługa klienta / serwisant / klient): "
    ).strip().lower()

    uzytkownik = Uzytkownik.query.filter_by(email=email).first()
    rola = Rola.query.filter_by(nazwa=nazwa_roli).first()

    if uzytkownik is None:
        print("Nie znaleziono użytkownika.")
    elif rola is None:
        print("Nie znaleziono roli.")
    elif rola in uzytkownik.role:
        print("Użytkownik ma już tę rolę.")
    else:
        try:
            uzytkownik.role.append(rola)
            db.session.commit()
            print(f"Przypisano rolę '{nazwa_roli}' użytkownikowi {email}.")
        except Exception:
            db.session.rollback()
            raise
