
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import app
from extensions import db
from models import Uzytkownik


with app.app_context():
    email = input("Podaj adres e-mail użytkownika: ").strip().lower()

    if not email:
        print("Adres e-mail nie może być pusty.")
        raise SystemExit(1)

    if Uzytkownik.query.filter_by(email=email).first():
        print("Użytkownik z tym adresem e-mail już istnieje.")
        raise SystemExit(1)

    haslo = getpass("Podaj hasło: ")
    powtorzone_haslo = getpass("Powtórz hasło: ")

    if len(haslo) < 12:
        print("Hasło musi mieć co najmniej 12 znaków.")
        raise SystemExit(1)

    if haslo != powtorzone_haslo:
        print("Hasła nie są identyczne.")
        raise SystemExit(1)

    imie = input("Podaj imię: ").strip()
    nazwisko = input("Podaj nazwisko: ").strip()

    if not imie or not nazwisko:
        print("Imię i nazwisko nie mogą być puste.")
        raise SystemExit(1)

    uzytkownik = Uzytkownik(
        email=email,
        haslo_hash=generate_password_hash(haslo),
        imie=imie,
        nazwisko=nazwisko,
        aktywny=True,
    )

    db.session.add(uzytkownik)
    db.session.commit()

    print(f"Utworzono konto użytkownika: {email}")
