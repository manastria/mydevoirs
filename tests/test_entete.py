import datetime
import re

import pytest

from mydevoirs.agenda import (
    Agenda,
    JourWidget,
    date_accueil,
    date_courte,
    debut_de_semaine,
    ecart_en_semaines,
    plage_de_dates,
    position_relative,
)

from .fixtures import *


def sans_markup(texte):
    """Texte du titre sans les balises Kivy ([size=...], [/size]...)."""
    return re.sub(r"\[/?[a-z]+(=[^\]]*)?\]", "", texte)

D = datetime.date
LUNDI, DIMANCHE = 0, 6


def test_date_courte():
    assert date_courte(D(2026, 10, 12)) == "12 octobre"
    assert date_courte(D(2026, 11, 1)) == "1er novembre"


@pytest.mark.parametrize(
    "jours, attendu",
    [
        ([D(2026, 10, 12), D(2026, 10, 13), D(2026, 10, 16)], "du 12 au 16 octobre"),
        ([D(2026, 9, 28), D(2026, 10, 2)], "du 28 septembre au 2 octobre"),
        ([D(2026, 10, 1), D(2026, 10, 2)], "du 1er au 2 octobre"),
        (
            [D(2026, 12, 28), D(2027, 1, 1)],
            "du 28 décembre 2026 au 1er janvier 2027",
        ),
        ([D(2026, 10, 12)], "le 12 octobre"),
        ([], ""),
    ],
)
def test_plage_de_dates(jours, attendu):
    assert plage_de_dates(jours) == attendu


def test_debut_de_semaine():
    jeudi = D(2026, 10, 15)
    assert debut_de_semaine(jeudi, LUNDI) == D(2026, 10, 12)
    assert debut_de_semaine(jeudi, DIMANCHE) == D(2026, 10, 11)
    assert debut_de_semaine(D(2026, 10, 11), DIMANCHE) == D(2026, 10, 11)


def test_ecart_en_semaines():
    jeudi = D(2026, 10, 15)
    assert ecart_en_semaines(jeudi, jeudi, LUNDI) == 0
    assert ecart_en_semaines(D(2026, 10, 18), jeudi, LUNDI) == 0  # dimanche
    assert ecart_en_semaines(D(2026, 10, 19), jeudi, LUNDI) == 1
    assert ecart_en_semaines(D(2026, 10, 18), jeudi, DIMANCHE) == 1
    assert ecart_en_semaines(D(2026, 9, 30), jeudi, LUNDI) == -2


@pytest.mark.parametrize(
    "ecart, attendu",
    [
        (0, "cette semaine"),
        (1, "semaine prochaine"),
        (-1, "semaine dernière"),
        (3, "dans 3 semaines"),
        (-2, "il y a 2 semaines"),
    ],
)
def test_position_relative(ecart, attendu):
    assert position_relative(ecart) == attendu


class TestDateAccueil(MyDevoirsTestCase):
    def test_semaine(self):
        self.app.config.set("agenda", "auto_next_week", "1")
        assert date_accueil(D(2026, 10, 15)) == D(2026, 10, 15)

    def test_week_end(self):
        self.app.config.set("agenda", "auto_next_week", "1")
        assert date_accueil(D(2026, 10, 17)) == D(2026, 10, 20)
        self.app.config.set("agenda", "auto_next_week", "0")
        assert date_accueil(D(2026, 10, 17)) == D(2026, 10, 17)


class TestJourWidgetAujourdhui(MyDevoirsTestCase):
    def setUp(self):
        super().setUp()
        from mydevoirs.app import MyDevoirsApp

        self.myapp = MyDevoirsApp()

    def tearDown(self):
        super().tearDown()
        self.myapp.stop()

    def test_aujourdhui(self):
        today = datetime.date.today()
        assert JourWidget(today).aujourdhui
        assert not JourWidget(today + datetime.timedelta(days=1)).aujourdhui


class TestEnTete(MyDevoirsTestCase):
    def setUp(self):
        super().setUp()
        # jours affichés et semaine suivante le week-end, indépendants du jour
        for jour in ("lundi", "mardi", "jeudi", "vendredi"):
            self.app.config.set("agenda", jour, "1")
        for jour in ("mercredi", "samedi", "dimanche"):
            self.app.config.set("agenda", jour, "0")
        self.app.config.set("agenda", "auto_next_week", "0")

    def test_titre_complet(self):
        agenda = Agenda()
        agenda.go_date(D(2027, 1, 6))
        texte = sans_markup(agenda.titre_semaine.text)
        assert texte.startswith("Semaine 1 (B) · du 4 au 8 janvier · ")

    def test_semaine_en_cours(self):
        agenda = Agenda()
        assert sans_markup(agenda.titre_semaine.text).endswith("· cette semaine")
        assert agenda.bouton_aujourdhui.opacity == 0
        assert agenda.bouton_aujourdhui.disabled

    def test_autre_semaine_et_retour(self):
        agenda = Agenda()
        agenda.go_date(datetime.date.today() + datetime.timedelta(weeks=2))
        assert sans_markup(agenda.titre_semaine.text).endswith("· dans 2 semaines")
        assert agenda.bouton_aujourdhui.opacity == 1
        assert not agenda.bouton_aujourdhui.disabled

        agenda.bouton_aujourdhui.dispatch("on_release")
        assert sans_markup(agenda.titre_semaine.text).endswith("· cette semaine")
        assert agenda.bouton_aujourdhui.opacity == 0

    def test_semaine_commencant_le_dimanche(self):
        # grille du dimanche 11 au samedi 17 octobre : c'est la semaine ISO 42,
        # même si le dimanche 11 appartient à la semaine ISO 41
        self.app.config.set("agenda", "start_day", "dimanche")
        self.app.config.set("agenda", "dimanche", "1")
        agenda = Agenda()
        agenda.go_date(D(2026, 10, 11))
        assert sans_markup(agenda.titre_semaine.text).startswith(
            "Semaine 42 (B) · du 11 au 16 octobre"
        )

    def test_changement_de_jour(self):
        agenda = Agenda()
        today = datetime.date.today()
        jours = [j for grille in agenda.carousel.slides for j in grille.children]
        for j in jours:
            j.aujourdhui = False  # état de la veille
        agenda._jour = today - datetime.timedelta(days=1)

        agenda._verifier_changement_de_jour()

        assert agenda._jour == today
        assert all(j.aujourdhui == (j.date == today) for j in jours)
