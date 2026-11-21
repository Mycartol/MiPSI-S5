
import os

from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
)
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from sqlalchemy import text
from werkzeug.security import check_password_hash

from extensions import db
from models import Uzytkownik, Zlecenie, Sprzet
from uprawnienia import wymaga_roli

import models  # noqa: E402


# Wczytanie zmiennych z pliku .env
load_dotenv()


# Inicjalizacja aplikacji Flask
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]


# Konfiguracja połączenia z PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg://{os.environ['DB_USER']}:"
    f"{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:"
    f"{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# Inicjalizacja SQLAlchemy
db.init_app(app)


# Inicjalizacja migracji
migrate = Migrate(app, db)


# Konfiguracja logowania
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Uzytkownik, int(user_id))


# ==========================================
# STRONA GŁÓWNA
# ==========================================

@app.route("/")
def home():
    try:
        result = db.session.execute(text("SELECT version()"))
        version = result.scalar()

        return (
            "<h1>Connected to PostgreSQL successfully!</h1>"
            f"<p>Database: {os.environ['DB_NAME']}</p>"
            f"<p>PostgreSQL version: {version}</p>"
        )

    except Exception:
        db.session.rollback()
        app.logger.exception("Database connection failed")

        return (
            "Database connection failed. "
            "Check your .env settings and PostgreSQL credentials."
        ), 500

    finally:
        db.session.remove()


# ==========================================
# LOGOWANIE
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        haslo = request.form.get("haslo", "")

        uzytkownik = Uzytkownik.query.filter_by(
            email=email
        ).first()

        if (
            uzytkownik is not None
            and check_password_hash(
                uzytkownik.haslo_hash,
                haslo
            )
        ):
            login_user(uzytkownik)
            return redirect(url_for("home"))

        return render_template(
            "login.html",
            blad="Nieprawidłowy adres e-mail lub hasło."
        ), 401

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# ==========================================
# UPRAWNIENIA
# ==========================================

@app.route("/test-admin")
@login_required
@wymaga_roli("admin")
def test_admin():

    return "<h1>Dostęp administratora potwierdzony!</h1>"


# ==========================================
# PANEL KLIENTA
# ==========================================

@app.route("/panel-klienta")
@login_required
@wymaga_roli("klient")
def panel_klienta():

    zlecenia = (
        Zlecenie.query
        .filter_by(klient_id=current_user.id)
        .order_by(Zlecenie.data_utworzenia.desc())
        .all()
    )

    return render_template(
        "panel_klienta.html",
        zlecenia=zlecenia,
    )


# ==========================================
# API - STATUS
# ==========================================

@app.route("/api/status", methods=["GET"])
def api_status():

    return {
        "status": "ok",
        "aplikacja": "System obsługi serwisu",
        "wersja": "1.0"
    }, 200


# ==========================================
# API - POBIERANIE ZLECEŃ (GET)
# ==========================================

@app.route("/api/zlecenia", methods=["GET"])
@login_required
def api_zlecenia():

    zlecenia = Zlecenie.query.order_by(
        Zlecenie.data_utworzenia.desc()
    ).all()

    wynik = []

    for z in zlecenia:

        wynik.append({
            "id": z.id,
            "klient_id": z.klient_id,
            "status": z.status,
            "data_utworzenia": (
                z.data_utworzenia.isoformat()
                if z.data_utworzenia else None
            )
        })

    return {
        "zlecenia": wynik,
        "liczba": len(wynik)
    }, 200


# ==========================================
# API - DODAWANIE ZLECENIA (POST)
# ==========================================

@app.route("/api/zlecenia", methods=["POST"])
@login_required
def api_dodaj_zlecenie():

    dane = request.get_json(silent=True)

    if not dane:
        return {
            "blad": "Brak danych JSON"
        }, 400

    tytul = dane.get("tytul")
    opis = dane.get("opis_problemu")
    sprzet_id = dane.get("sprzet_id")

    if not tytul or not opis or not sprzet_id:
        return {
            "blad": "Wymagane pola: tytul, opis_problemu, sprzet_id"
        }, 400

    # Sprawdzenie, czy sprzęt należy do zalogowanego użytkownika
    sprzet = Sprzet.query.filter_by(
        id=sprzet_id,
        wlasciciel_id=current_user.id
    ).first()

    if sprzet is None:
        return {
            "blad": "Nie znaleziono sprzętu klienta"
        }, 404

    try:

        zlecenie = Zlecenie(
            klient_id=current_user.id,
            sprzet_id=sprzet.id,
            tytul=tytul,
            opis_problemu=opis,
            status="nowe",
            priorytet="normalny"
        )

        db.session.add(zlecenie)
        db.session.commit()

        return {
            "komunikat": "Zgłoszenie zostało utworzone",
            "id": zlecenie.id,
            "status": zlecenie.status
        }, 201

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Błąd tworzenia zgłoszenia"
        )

        return {
            "blad": "Nie udało się utworzyć zgłoszenia"
        }, 500


# ==========================================
# API - AKTUALIZACJA ZLECENIA (PUT)
# ==========================================

@app.route("/api/zlecenia/<int:zlecenie_id>", methods=["PUT"])
@login_required
def api_aktualizuj_zlecenie(zlecenie_id):

    dane = request.get_json(silent=True)

    if not dane:
        return {
            "blad": "Brak danych JSON"
        }, 400

    # Pobranie zgłoszenia należącego do zalogowanego klienta
    zlecenie = Zlecenie.query.filter_by(
        id=zlecenie_id,
        klient_id=current_user.id
    ).first()

    if zlecenie is None:
        return {
            "blad": "Nie znaleziono zgłoszenia"
        }, 404

    tytul = dane.get("tytul")
    opis = dane.get("opis_problemu")

    if not tytul or not opis:
        return {
            "blad": "Wymagane pola: tytul, opis_problemu"
        }, 400

    try:

        zlecenie.tytul = tytul
        zlecenie.opis_problemu = opis

        db.session.commit()

        return {
            "komunikat": "Zgłoszenie zostało zaktualizowane",
            "id": zlecenie.id,
            "status": zlecenie.status
        }, 200

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Błąd aktualizacji zgłoszenia"
        )

        return {
            "blad": "Nie udało się zaktualizować zgłoszenia"
        }, 500


@app.route("/api/zlecenia/<int:zlecenie_id>", methods=["DELETE"])
@login_required
def api_usun_zlecenie(zlecenie_id):

    zlecenie = Zlecenie.query.filter_by(
        id=zlecenie_id,
        klient_id=current_user.id
    ).first()

    if zlecenie is None:
        return {
            "blad": "Nie znaleziono zgłoszenia"
        }, 404

    try:

        db.session.delete(zlecenie)
        db.session.commit()

        return {
            "komunikat": "Zgłoszenie zostało usunięte",
            "id": zlecenie_id
        }, 200

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Błąd usuwania zgłoszenia"
        )

        return {
            "blad": "Nie udało się usunąć zgłoszenia"
        }, 500

if __name__ == "__main__":
    app.run(debug=True)
