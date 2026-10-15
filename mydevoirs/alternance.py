"""
Alternance des semaines (A/B, ou tout autre cycle).

La lettre d'une semaine se déduit de son écart, en semaines, avec un lundi de
référence qui porte la première lettre du cycle. Contrairement à la parité du
numéro ISO, ce calcul ne casse pas au passage d'une année de 53 semaines.
"""
import datetime
from typing import List

from mydevoirs.utils import get_config

LIBELLES_PAR_DEFAUT = "A, B"

# Lundi de la semaine ISO 1 de 2026 : conserve les lettres de la version 1.3.0
# (semaine impaire = A) jusqu'à la fin de 2026.
REFERENCE_PAR_DEFAUT = "2025-12-29"


def lundi(jour: datetime.date) -> datetime.date:
    return jour - datetime.timedelta(days=jour.weekday())


def parse_libelles(texte: str) -> List[str]:
    """ "A, B" -> ["A", "B"] ; les libellés vides sont ignorés."""
    return [x.strip() for x in (texte or "").split(",") if x.strip()]


def parse_reference(texte: str) -> datetime.date:
    """Lundi de référence enregistré, ou celui par défaut s'il est illisible."""
    try:
        jour = datetime.date.fromisoformat(texte)
    except (TypeError, ValueError):
        jour = datetime.date.fromisoformat(REFERENCE_PAR_DEFAUT)
    return lundi(jour)


def lettre_semaine(
    jour: datetime.date, reference: datetime.date, libelles: List[str]
) -> str:
    if not libelles:
        return ""
    index = ((lundi(jour) - lundi(reference)).days // 7) % len(libelles)
    return libelles[index]


def reference_pour(
    jour: datetime.date, lettre: str, libelles: List[str]
) -> datetime.date:
    """Lundi de référence tel que la semaine de `jour` porte `lettre`."""
    return lundi(jour) - datetime.timedelta(weeks=libelles.index(lettre))


def libelles_configures() -> List[str]:
    return parse_libelles(
        get_config("agenda", "alternance_libelles", str, LIBELLES_PAR_DEFAUT)
    )


def lettre_configuree(jour: datetime.date) -> str:
    """Lettre de la semaine de `jour` selon les réglages, "" si désactivée."""
    if not get_config("agenda", "alternance", bool, True):
        return ""
    reference = parse_reference(
        get_config("agenda", "alternance_reference", str, REFERENCE_PAR_DEFAUT)
    )
    return lettre_semaine(jour, reference, libelles_configures())
