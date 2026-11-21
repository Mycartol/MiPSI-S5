
from functools import wraps

from flask import abort
from flask_login import current_user


def wymaga_roli(*dozwolone_role):
    """
    Pozwala wejść na stronę użytkownikom, którzy mają
    przynajmniej jedną z podanych ról.
    """

    def dekorator(funkcja):
        @wraps(funkcja)
        def opakowanie(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            nazwy_ról_użytkownika = {
                rola.nazwa for rola in current_user.role
            }

            if not nazwy_ról_użytkownika.intersection(dozwolone_role):
                abort(403)

            return funkcja(*args, **kwargs)

        return opakowanie

    return dekorator
