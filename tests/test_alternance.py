import datetime
import re

import freezegun
import pytest
from kivy.uix.settings import SettingsPanel
from kivy.uix.togglebutton import ToggleButton

from mydevoirs.agenda import Agenda
from mydevoirs.alternance import (
    REFERENCE_PAR_DEFAUT,
    lettre_configuree,
    lettre_semaine,
    lundi,
    parse_libelles,
    parse_reference,
    reference_pour,
)
from mydevoirs.custom_setting import SettingSemaineCourante

from .fixtures import *


def sans_markup(texte):
    """Texte du titre sans les balises Kivy ([size=...], [/size]...)."""
    return re.sub(r"\[/?[a-z]+(=[^\]]*)?\]", "", texte)

D = datetime.date
AB = ["A", "B"]
DEFAUT = D.fromisoformat(REFERENCE_PAR_DEFAUT)


def test_lundi():
    assert lundi(D(2026, 10, 15)) == D(2026, 10, 12)  # jeudi
    assert lundi(D(2026, 10, 12)) == D(2026, 10, 12)
    assert lundi(D(2026, 10, 18)) == D(2026, 10, 12)  # dimanche


@pytest.mark.parametrize(
    "texte, attendu",
    [
        ("A, B", ["A", "B"]),
        ("1,2,3", ["1", "2", "3"]),
        (" Paire , Impaire ,", ["Paire", "Impaire"]),
        ("", []),
        (None, []),
    ],
)
def test_parse_libelles(texte, attendu):
    assert parse_libelles(texte) == attendu


def test_parse_reference():
    assert parse_reference("2026-10-12") == D(2026, 10, 12)
    assert parse_reference("2026-10-15") == D(2026, 10, 12)  # ramené au lundi
    assert parse_reference("n'importe quoi") == DEFAUT
    assert parse_reference(None) == DEFAUT


def test_defaut_conserve_la_regle_1_3_0_en_2026():
    """Semaine ISO impaire = A, comme la version 1.3.0, pour toute l'année 2026."""
    for semaine in range(1, 54):
        jour = D.fromisocalendar(2026, semaine, 1)
        assert lettre_semaine(jour, DEFAUT, AB) == ("A" if semaine % 2 else "B")


def test_passage_2026_2027_sans_a_coup():
    # 2026 compte 53 semaines : la parité ISO donnait A, A le 28/12 puis le 04/01.
    assert [
        lettre_semaine(D(2026, 12, 21), DEFAUT, AB),
        lettre_semaine(D(2026, 12, 28), DEFAUT, AB),
        lettre_semaine(D(2027, 1, 4), DEFAUT, AB),
        lettre_semaine(D(2027, 1, 11), DEFAUT, AB),
    ] == ["B", "A", "B", "A"]


def test_alternance_continue_sur_plusieurs_annees():
    jour = DEFAUT
    precedente = lettre_semaine(jour, DEFAUT, AB)
    for _ in range(52 * 12):
        jour += datetime.timedelta(weeks=1)
        lettre = lettre_semaine(jour, DEFAUT, AB)
        assert lettre != precedente
        precedente = lettre


def test_tous_les_jours_de_la_semaine_ont_la_meme_lettre():
    ref = D(2026, 10, 12)
    assert {lettre_semaine(ref + datetime.timedelta(days=i), ref, AB) for i in range(7)} == {"A"}


def test_cycle_de_trois_semaines():
    ref = D(2026, 10, 12)
    lettres = [
        lettre_semaine(ref + datetime.timedelta(weeks=i), ref, ["1", "2", "3"])
        for i in range(-3, 4)
    ]
    assert lettres == ["1", "2", "3", "1", "2", "3", "1"]


def test_dates_avant_la_reference():
    ref = D(2026, 10, 12)
    assert lettre_semaine(D(2026, 10, 5), ref, AB) == "B"
    assert lettre_semaine(D(2026, 9, 28), ref, AB) == "A"


def test_sans_libelle():
    assert lettre_semaine(D(2026, 10, 12), DEFAUT, []) == ""


@pytest.mark.parametrize("lettre", ["1", "2", "3"])
def test_reference_pour(lettre):
    libelles = ["1", "2", "3"]
    jour = D(2026, 10, 15)
    ref = reference_pour(jour, lettre, libelles)
    assert ref.weekday() == 0
    assert lettre_semaine(jour, ref, libelles) == lettre


class TestLettreConfiguree(MyDevoirsTestCase):
    def test_defaut(self):
        assert lettre_configuree(D(2026, 10, 15)) == "B"  # semaine 42

    def test_desactivee(self):
        self.app.config.set("agenda", "alternance", "0")
        assert lettre_configuree(D(2026, 10, 15)) == ""

    def test_reglages(self):
        self.app.config.set("agenda", "alternance_libelles", "1, 2, 3")
        self.app.config.set("agenda", "alternance_reference", "2026-10-12")
        assert lettre_configuree(D(2026, 10, 15)) == "1"
        assert lettre_configuree(D(2026, 10, 22)) == "2"
        assert lettre_configuree(D(2026, 10, 29)) == "3"


class TestAgendaEnTete(MyDevoirsTestCase):
    def test_lettre_dans_le_titre(self):
        agenda = Agenda()
        agenda.go_date(D(2027, 1, 6))
        assert sans_markup(agenda.titre_semaine.text).startswith("Semaine 1 (B)")

    def test_desactivee_aucune_lettre(self):
        self.app.config.set("agenda", "alternance", "0")
        agenda = Agenda()
        agenda.go_date(D(2027, 1, 6))
        assert sans_markup(agenda.titre_semaine.text).startswith("Semaine 1 · ")

    def test_changement_de_reglage_met_a_jour(self):
        agenda = Agenda()
        agenda.go_date(D(2027, 1, 6))
        self.app.config.set("agenda", "alternance_libelles", "Paire, Impaire")
        agenda.go_date(D(2027, 1, 6))  # ce que fait on_config_change_agenda
        assert sans_markup(agenda.titre_semaine.text).startswith("Semaine 1 (Impaire)")

    def test_libelle_avec_crochets(self):
        self.app.config.set("agenda", "alternance_libelles", "[A], [B]")
        agenda = Agenda()
        agenda.go_date(D(2027, 1, 6))
        assert sans_markup(agenda.titre_semaine.text).startswith("Semaine 1 (&bl;B&br;)")


class TestSettingSemaineCourante(MyDevoirsTestCase):
    def setUp(self):
        super().setUp()
        self.panel = SettingsPanel(config=self.app.config)
        self.setting = SettingSemaineCourante(
            panel=self.panel, section="agenda", key="alternance_reference"
        )

    @freezegun.freeze_time("2026-10-15")
    def test_affiche_la_lettre_et_non_la_date(self):
        self.setting._refresh_lettre()
        assert self.setting.lettre == "B"

    @freezegun.freeze_time("2026-10-15")
    def test_choisir_la_lettre(self):
        self.setting._create_popup(self.setting)
        boutons = [
            w for w in self.setting.popup.content.children if isinstance(w, ToggleButton)
        ]
        assert sorted(b.text for b in boutons) == ["A", "B"]
        bouton_a = next(b for b in boutons if b.text == "A")
        assert bouton_a.state == "normal"

        bouton_a.dispatch("on_release")

        assert self.setting.lettre == "A"
        assert self.app.config.get("agenda", "alternance_reference") == "2026-10-12"
        assert lettre_configuree(D(2026, 10, 15)) == "A"
        assert lettre_configuree(D(2026, 10, 22)) == "B"
