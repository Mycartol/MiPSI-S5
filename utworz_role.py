
from app import app
from extensions import db
from models import Rola


role_do_utworzenia = [
    {
        "nazwa": "admin",
        "opis": "Pełny dostęp do systemu.",
    },
    {
        "nazwa": "obsługa klienta",
        "opis": "Obsługa zgłoszeń i kontakt z klientami.",
    },
    {
        "nazwa": "serwisant",
        "opis": "Realizacja przydzielonych napraw.",
    },
    {
        "nazwa": "klient",
        "opis": "Tworzenie zgłoszeń i sprawdzanie ich statusu.",
    },
]


with app.app_context():
    try:
        for dane_roli in role_do_utworzenia:
            istnieje = Rola.query.filter_by(
                nazwa=dane_roli["nazwa"]
            ).first()

            if istnieje is None:
                rola = Rola(
                    nazwa=dane_roli["nazwa"],
                    opis=dane_roli["opis"],
                )
                db.session.add(rola)
                print(f"Dodano rolę: {dane_roli['nazwa']}")
            else:
                print(f"Rola już istnieje: {dane_roli['nazwa']}")

        db.session.commit()
        print("Zakończono tworzenie ról.")

    except Exception:
        db.session.rollback()
        raise
