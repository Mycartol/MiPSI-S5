
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from extensions import db
from flask_login import UserMixin



uzytkownicy_role = db.Table(
    "uzytkownicy_role",
    db.Column(
        "uzytkownik_id",
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        primary_key=True,
    ),
    db.Column(
        "rola_id",
        db.BigInteger,
        db.ForeignKey("role.id"),
        primary_key=True,
    ),
    db.Column(
        "data_przypisania",
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    ),
)


class Uzytkownik(UserMixin, db.Model):
    __tablename__ = "uzytkownicy"

    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    haslo_hash = db.Column(db.String(255), nullable=False)
    imie = db.Column(db.String(100), nullable=False)
    nazwisko = db.Column(db.String(100), nullable=False)
    aktywny = db.Column(db.Boolean, nullable=False, default=True)
    data_utworzenia = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    role = db.relationship(
        "Rola",
        secondary=uzytkownicy_role,
        back_populates="uzytkownicy",
    )

    sprzety = db.relationship(
        "Sprzet",
        back_populates="wlasciciel",
        foreign_keys="Sprzet.wlasciciel_id",
    )

    zlecenia_klienta = db.relationship(
        "Zlecenie",
        back_populates="klient",
        foreign_keys="Zlecenie.klient_id",
    )

    zlecenia_obslugiwane = db.relationship(
        "Zlecenie",
        back_populates="obslugujacy",
        foreign_keys="Zlecenie.obslugujacy_id",
    )

    zlecenia_serwisowane = db.relationship(
        "Zlecenie",
        back_populates="serwisant",
        foreign_keys="Zlecenie.serwisant_id",
    )

    zalaczniki = db.relationship(
        "Zalacznik",
        back_populates="dodajacy",
    )

    historia_zmian = db.relationship(
        "HistoriaStatusow",
        back_populates="zmieniajacy",
    )

    grafiki = db.relationship(
        "Grafik",
        back_populates="uzytkownik",
    )

    kontakty = db.relationship(
        "Kontakt",
        back_populates="uzytkownik",
        cascade="all, delete-orphan",
    )


class Rola(db.Model):
    __tablename__ = "role"

    id = db.Column(db.BigInteger, primary_key=True)
    nazwa = db.Column(db.String(50), nullable=False, unique=True)
    opis = db.Column(db.Text)

    uzytkownicy = db.relationship(
        "Uzytkownik",
        secondary=uzytkownicy_role,
        back_populates="role",
    )



class Sprzet(db.Model):
    __tablename__ = "sprzet"

    id = db.Column(db.BigInteger, primary_key=True)
    wlasciciel_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=False,
    )
    nazwa = db.Column(db.String(150), nullable=False)
    producent = db.Column(db.String(100))
    model = db.Column(db.String(100))
    numer_seryjny = db.Column(db.String(150))
    opis = db.Column(db.Text)
    data_dodania = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    wlasciciel = db.relationship(
        "Uzytkownik",
        back_populates="sprzety",
        foreign_keys=[wlasciciel_id],
    )

    zlecenia = db.relationship(
        "Zlecenie",
        back_populates="sprzet",
    )


class Zlecenie(db.Model):
    __tablename__ = "zlecenia"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('nowe', 'oczekuje_na_diagnoze', "
            "'oczekuje_na_czesci', 'w_trakcie', "
            "'zakonczone', 'anulowane')",
            name="ck_zlecenia_status",
        ),
        db.CheckConstraint(
            "priorytet IN ('niski', 'normalny', 'wysoki', 'pilny')",
            name="ck_zlecenia_priorytet",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    klient_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=False,
    )
    sprzet_id = db.Column(
        db.BigInteger,
        db.ForeignKey("sprzet.id"),
        nullable=False,
    )
    obslugujacy_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
    )
    serwisant_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
    )

    tytul = db.Column(db.String(200), nullable=False)
    opis_problemu = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), nullable=False, default="nowe")
    priorytet = db.Column(
        db.String(20),
        nullable=False,
        default="normalny",
    )
    data_utworzenia = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    termin_realizacji = db.Column(db.DateTime(timezone=True))
    data_zakonczenia = db.Column(db.DateTime(timezone=True))

    klient = db.relationship(
        "Uzytkownik",
        back_populates="zlecenia_klienta",
        foreign_keys=[klient_id],
    )
    sprzet = db.relationship("Sprzet", back_populates="zlecenia")
    obslugujacy = db.relationship(
        "Uzytkownik",
        back_populates="zlecenia_obslugiwane",
        foreign_keys=[obslugujacy_id],
    )
    serwisant = db.relationship(
        "Uzytkownik",
        back_populates="zlecenia_serwisowane",
        foreign_keys=[serwisant_id],
    )

    zalaczniki = db.relationship(
        "Zalacznik",
        back_populates="zlecenie",
        cascade="all, delete-orphan",
    )
    historia_statusow = db.relationship(
        "HistoriaStatusow",
        back_populates="zlecenie",
        cascade="all, delete-orphan",
    )
    czesci = db.relationship(
        "ZlecenieCzesc",
        back_populates="zlecenie",
        cascade="all, delete-orphan",
    )
    uslugi = db.relationship(
        "ZlecenieUsluga",
        back_populates="zlecenie",
        cascade="all, delete-orphan",
    )
    dane_dostawy = db.relationship(
        "DaneDostawy",
        back_populates="zlecenie",
        cascade="all, delete-orphan",
    )


class Zalacznik(db.Model):
    __tablename__ = "zalaczniki"

    id = db.Column(db.BigInteger, primary_key=True)
    zlecenie_id = db.Column(
        db.BigInteger,
        db.ForeignKey("zlecenia.id"),
        nullable=False,
    )
    dodajacy_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=False,
    )
    nazwa_pliku = db.Column(db.String(255), nullable=False)
    sciezka_pliku = db.Column(db.String(500), nullable=False)
    typ_mime = db.Column(db.String(100))
    data_dodania = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    zlecenie = db.relationship("Zlecenie", back_populates="zalaczniki")
    dodajacy = db.relationship("Uzytkownik", back_populates="zalaczniki")


class HistoriaStatusow(db.Model):
    __tablename__ = "historia_statusow"

    id = db.Column(db.BigInteger, primary_key=True)
    zlecenie_id = db.Column(
        db.BigInteger,
        db.ForeignKey("zlecenia.id"),
        nullable=False,
    )
    zmieniajacy_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
    )
    poprzedni_status = db.Column(db.String(40))
    nowy_status = db.Column(db.String(40), nullable=False)
    komentarz = db.Column(db.Text)
    data_zmiany = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    zlecenie = db.relationship(
        "Zlecenie",
        back_populates="historia_statusow",
    )
    zmieniajacy = db.relationship(
        "Uzytkownik",
        back_populates="historia_zmian",
    )


class Magazyn(db.Model):
    __tablename__ = "magazyn"

    id = db.Column(db.BigInteger, primary_key=True)
    nazwa = db.Column(db.String(150), nullable=False)
    lokalizacja = db.Column(db.String(255))
    opis = db.Column(db.Text)
    aktywny = db.Column(db.Boolean, nullable=False, default=True)

    stany = db.relationship(
        "StanMagazynowy",
        back_populates="magazyn",
        cascade="all, delete-orphan",
    )


class CzescMagazyn(db.Model):
    # Katalog części; ilości w poszczególnych magazynach
    # przechowuje tabela StanMagazynowy.
    __tablename__ = "czesci_magazyn"

    __table_args__ = (
        db.CheckConstraint(
            "cena_jednostkowa >= 0",
            name="ck_czesci_cena",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    nazwa = db.Column(db.String(200), nullable=False)
    numer_katalogowy = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )
    opis = db.Column(db.Text)
    cena_jednostkowa = db.Column(db.Numeric(12, 2), nullable=False)
    jednostka = db.Column(
        db.String(20),
        nullable=False,
        default="szt.",
    )
    aktywny = db.Column(db.Boolean, nullable=False, default=True)

    stany = db.relationship(
        "StanMagazynowy",
        back_populates="czesc",
        cascade="all, delete-orphan",
    )


class StanMagazynowy(db.Model):
    __tablename__ = "stan_magazynowy"

    __table_args__ = (
        db.CheckConstraint("ilosc >= 0", name="ck_stan_ilosc"),
    )

    magazyn_id = db.Column(
        db.BigInteger,
        db.ForeignKey("magazyn.id"),
        primary_key=True,
    )
    czesc_id = db.Column(
        db.BigInteger,
        db.ForeignKey("czesci_magazyn.id"),
        primary_key=True,
    )
    ilosc = db.Column(db.Integer, nullable=False, default=0)
    data_aktualizacji = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    magazyn = db.relationship("Magazyn", back_populates="stany")
    czesc = db.relationship("CzescMagazyn", back_populates="stany")


class ZlecenieCzesc(db.Model):
    __tablename__ = "zlecenia_czesci"

    __table_args__ = (
        db.CheckConstraint("ilosc > 0", name="ck_zlecenia_czesci_ilosc"),
        db.CheckConstraint(
            "cena_w_chwili_uzycia >= 0",
            name="ck_zlecenia_czesci_cena",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    zlecenie_id = db.Column(
        db.BigInteger,
        db.ForeignKey("zlecenia.id"),
        nullable=False,
    )
    czesc_id = db.Column(
        db.BigInteger,
        db.ForeignKey("czesci_magazyn.id"),
        nullable=False,
    )
    ilosc = db.Column(db.Integer, nullable=False)
    cena_w_chwili_uzycia = db.Column(db.Numeric(12, 2), nullable=False)

    zlecenie = db.relationship("Zlecenie", back_populates="czesci")
    czesc = db.relationship("CzescMagazyn")



class Usluga(db.Model):
    __tablename__ = "uslugi"

    __table_args__ = (
        db.CheckConstraint("cena_bazowa >= 0", name="ck_uslugi_cena"),
        db.CheckConstraint(
            "czas_szacowany_min IS NULL OR czas_szacowany_min > 0",
            name="ck_uslugi_czas",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    nazwa = db.Column(db.String(150), nullable=False, unique=True)
    opis = db.Column(db.Text)
    cena_bazowa = db.Column(db.Numeric(12, 2), nullable=False)
    czas_szacowany_min = db.Column(db.Integer)
    aktywna = db.Column(db.Boolean, nullable=False, default=True)


class ZlecenieUsluga(db.Model):
    __tablename__ = "zlecenia_uslugi"

    __table_args__ = (
        db.CheckConstraint(
            "cena_w_chwili_zlecenia >= 0",
            name="ck_zlecenia_uslugi_cena",
        ),
        db.CheckConstraint(
            "status_wykonania IN ('oczekuje', 'w_trakcie', "
            "'wykonana', 'anulowana')",
            name="ck_zlecenia_uslugi_status",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    zlecenie_id = db.Column(
        db.BigInteger,
        db.ForeignKey("zlecenia.id"),
        nullable=False,
    )
    usluga_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uslugi.id"),
        nullable=False,
    )
    cena_w_chwili_zlecenia = db.Column(db.Numeric(12, 2), nullable=False)
    status_wykonania = db.Column(
        db.String(30),
        nullable=False,
        default="oczekuje",
    )

    zlecenie = db.relationship("Zlecenie", back_populates="uslugi")
    usluga = db.relationship("Usluga")


class Grafik(db.Model):
    __tablename__ = "grafiki"

    __table_args__ = (
        db.CheckConstraint(
            "data_zakonczenia > data_rozpoczecia",
            name="ck_grafiki_przedzial_czasu",
        ),
        db.CheckConstraint(
            "status IN ('zaplanowana', 'zatwierdzona', 'odwolana')",
            name="ck_grafiki_status",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    uzytkownik_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=False,
    )
    data_rozpoczecia = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    data_zakonczenia = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    typ_zmiany = db.Column(db.String(30), nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="zaplanowana",
    )
    uwagi = db.Column(db.Text)

    uzytkownik = db.relationship("Uzytkownik", back_populates="grafiki")


# =========================================================
# KONTAKTY
# =========================================================

class Kontakt(db.Model):
    __tablename__ = "kontakt"

    __table_args__ = (
        db.CheckConstraint(
            "typ IN ('telefon', 'email', 'inny')",
            name="ck_kontakt_typ",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    uzytkownik_id = db.Column(
        db.BigInteger,
        db.ForeignKey("uzytkownicy.id"),
        nullable=False,
    )
    typ = db.Column(db.String(30), nullable=False)
    wartosc = db.Column(db.String(255), nullable=False)
    preferowany = db.Column(db.Boolean, nullable=False, default=False)

    uzytkownik = db.relationship("Uzytkownik", back_populates="kontakty")


# =========================================================
# DANE DOSTAWY / ODBIORU
# =========================================================

class DaneDostawy(db.Model):
    __tablename__ = "dane_dostawy"

    __table_args__ = (
        db.CheckConstraint(
            "typ_dostawy IN ('odbior', 'zwrot', 'dostawa', 'inny')",
            name="ck_dane_dostawy_typ",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    zlecenie_id = db.Column(
        db.BigInteger,
        db.ForeignKey("zlecenia.id"),
        nullable=False,
    )
    typ_dostawy = db.Column(db.String(30), nullable=False)
    odbiorca = db.Column(db.String(200), nullable=False)
    telefon = db.Column(db.String(30), nullable=False)
    ulica = db.Column(db.String(150), nullable=False)
    numer_budynku = db.Column(db.String(20), nullable=False)
    numer_lokalu = db.Column(db.String(20))
    kod_pocztowy = db.Column(db.String(15), nullable=False)
    miasto = db.Column(db.String(100), nullable=False)
    kraj = db.Column(db.String(100), nullable=False, default="Polska")

    zlecenie = db.relationship(
        "Zlecenie",
        back_populates="dane_dostawy",
    )
