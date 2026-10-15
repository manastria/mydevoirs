import datetime
import itertools
from typing import List

from kivy.app import App
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.utils import escape_markup
from pony.orm import db_session
from kivy.clock import Clock

from mydevoirs.alternance import lettre_configuree
from mydevoirs.constants import SEMAINE
from mydevoirs.database import db
from mydevoirs.itemwidget import ItemWidget
from mydevoirs.matieredropdown import MatiereDropdown
from mydevoirs.utils import get_config


def jour_du_mois(jour: datetime.date) -> str:
    return "1er" if jour.day == 1 else str(jour.day)


def date_courte(jour: datetime.date) -> str:
    """12 octobre, 1er novembre"""
    return f"{jour_du_mois(jour)} {jour.strftime('%B')}"


def plage_de_dates(jours: List[datetime.date]) -> str:
    """du 12 au 16 octobre, du 28 septembre au 2 octobre..."""
    if not jours:
        return ""
    debut, fin = min(jours), max(jours)
    if debut == fin:
        return f"le {date_courte(debut)}"
    if debut.year != fin.year:
        return f"du {date_courte(debut)} {debut.year} au {date_courte(fin)} {fin.year}"
    if debut.month == fin.month:
        return f"du {jour_du_mois(debut)} au {date_courte(fin)}"
    return f"du {date_courte(debut)} au {date_courte(fin)}"


def debut_de_semaine(jour: datetime.date, start_day: int) -> datetime.date:
    """Premier jour de la grille contenant `jour` (start_day : 0 = lundi)."""
    return jour - datetime.timedelta(days=(jour.weekday() - start_day) % 7)


def ecart_en_semaines(jour: datetime.date, reference: datetime.date, start_day: int) -> int:
    return (
        debut_de_semaine(jour, start_day) - debut_de_semaine(reference, start_day)
    ).days // 7


def position_relative(ecart: int) -> str:
    if ecart == 0:
        return "cette semaine"
    if ecart == 1:
        return "semaine prochaine"
    if ecart == -1:
        return "semaine dernière"
    if ecart > 1:
        return f"dans {ecart} semaines"
    return f"il y a {-ecart} semaines"


def titre_semaine(
    lundi: datetime.date, jours_affiches: List[datetime.date], ecart: int
) -> str:
    """Titre de l'en-tête (markup Kivy) pour la grille contenant `lundi`."""
    semaine = f"Semaine {lundi.isocalendar()[1]}"
    lettre = lettre_configuree(lundi)
    if lettre:
        semaine += f" ({escape_markup(lettre)})"
    # Pas de gras : les polices fournies n'existent qu'en version normale
    parties = [
        f"[size=18sp]{semaine}[/size]",
        plage_de_dates(jours_affiches),
        position_relative(ecart),
    ]
    return " · ".join(p for p in parties if p)


def start_day_configure() -> int:
    return SEMAINE.index(get_config("agenda", "start_day", str, "lundi"))


def date_accueil(aujourdhui: datetime.date = None) -> datetime.date:
    """Date montrée à l'ouverture : le week-end, la semaine suivante si réglé."""
    jour = aujourdhui or datetime.date.today()
    if jour.weekday() in (5, 6) and get_config("agenda", "auto_next_week", bool, False):
        return jour + datetime.timedelta(days=3)
    return jour


class AgendaItemWidget(ItemWidget):
    def __init__(self, **kwargs):
        self._jour_widget = None
        super().__init__(**kwargs)

    def on_done(self, *args):
        super().on_done(*args)
        if self.loaded_flag:
            self.jour_widget.update_progression()

    @property
    def jour_widget(self):
        if not self._jour_widget:
            for x in self.walk_reverse():
                if isinstance(x, JourWidget) and x.date == self.date:
                    self._jour_widget = x
        return self._jour_widget

    def remove_after_confirmation(self):
        # need to backup JourWidget before del to call update_progression
        jour = self.jour_widget
        super().remove_after_confirmation()
        jour.update_progression()


class JourItems(BoxLayout):
    def __init__(self, date):
        super().__init__()
        self.date = date

        with db_session:
            query = db.Item.select(
                lambda x: x.jour.date == date
            )  # pragma: no cover_all
            widgets = [AgendaItemWidget(**i.to_dict()) for i in query]
        for item in widgets:
            self.add_widget(item)


class JourWidget(BoxLayout):

    progression = StringProperty("0/0")
    aujourdhui = BooleanProperty(False)

    def __init__(self, date, **kwargs):
        self.date = date  # need in nice_date
        super().__init__(**kwargs)
        self.aujourdhui = date == datetime.date.today()

        self.jouritem = JourItems(date)
        self.jouritem.bind(minimum_height=self.jouritem.setter("height"))
        self.ids.scroll_items.add_widget(self.jouritem)
        self.update_progression()

    def update_progression(self):
        with db_session:
            pro = db.Jour.get_or_create(date=self.date).progression
            self.progression = f"{pro[0]}/{pro[1]}"

    @property
    def nice_date(self):
        # semaine et année sont dans l'en-tête de l'agenda
        return f"{self.date.strftime('%A')} {date_courte(self.date)}"

    def add_item(self):
        with db_session:
            jour = db.Jour.get_or_create(date=self.date)
            matiere = db.Matiere.select().first()
            item = db.Item(jour=jour, matiere=matiere)

            item_widget = AgendaItemWidget(**item.to_dict())
        self.jouritem.add_widget(item_widget)
        self.update_progression()
        MatiereDropdown().open(item_widget)

    @property
    def items(self):
        return self.jouritem.children


class BaseGrid(GridLayout):
    number_to_show = NumericProperty()

    def __init__(self, day=None):
        self.day = day or datetime.date.today()
        super().__init__(cols=2)
        self.build_grid(self.get_days_to_show())

    def __repr__(self):
        return f"BaseGrid : {self.day}"

    def get_week_days(self, shown_days: List[bool], start_day: int):
        return self._get_week_days(self.day, start_day, shown_days)

    @staticmethod
    def _get_week_days(day, start_day, jours_actifs):
        delta = (
            day.weekday() - start_day
            if day.weekday() >= start_day
            else 7 - (start_day - day.weekday())
        )
        start_date = day - datetime.timedelta(days=delta)
        days = [start_date + datetime.timedelta(days=i) for i in range(7)]
        jours = jours_actifs[start_day:] + jours_actifs[:start_day]
        return itertools.compress(days, jours)

    @staticmethod
    def get_days_to_show():
        return [get_config("agenda", j, bool, True) for j in SEMAINE]

    def build_grid(self, days_to_show: List[bool]):
        for d in self.get_week_days(days_to_show, start_day_configure()):
            self.add_widget(JourWidget(d))


class CarouselWidget(Carousel):
    # def on_slides(self, *args):
    #     pass

    def __init__(self, day=None):
        self._removing = False
        self._init = True
        self.date = day or date_accueil()

        super().__init__()
        self.add_widget(BaseGrid(self.date - datetime.timedelta(weeks=1)))
        self.add_widget(BaseGrid(self.date))
        self.add_widget(BaseGrid(self.date + datetime.timedelta(weeks=1)))

        self.index = 1

    def on_index(self, *args):
        if self._init:
            self._init = False
            return
        if self._removing:
            return

        super().on_index(*args)

        index = args[1]

        if index == 1:
            return

            # else:
        sens = 0 if index else -1

        # can't remove the if statement/don't why.
        if index:
            # build right
            self.add_widget(
                BaseGrid(self.slides[index].day + datetime.timedelta(weeks=1)), sens
            )
            self._removing = True
            self.remove_widget(self.slides[sens])

        else:
            # build left
            self.add_widget(
                BaseGrid(self.slides[index].day - datetime.timedelta(weeks=1)), sens
            )
            self.remove_widget(self.slides[sens])

        self.index = 1
        self.date = self.current_slide.day
        self._removing = False


class Agenda(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.add_widget(self.layout)

        # En-tête : semaine affichée, retour à aujourd'hui, saut vers une date
        self.header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=30,
            spacing=5,
            padding=(8, 0, 0, 0),
        )

        police = getattr(App.get_running_app(), "theme", {}).get("police")
        avec_police = {"font_name": police} if police else {}
        self.titre_semaine = Label(
            markup=True,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
            **avec_police,
        )
        self.titre_semaine.bind(size=self.titre_semaine.setter("text_size"))

        # Visible seulement hors de la semaine montrée à l'ouverture
        self.bouton_aujourdhui = Button(
            text="Aujourd'hui", size_hint_x=None, width=120, **avec_police
        )
        self.bouton_aujourdhui.bind(on_release=lambda *args: self.go_date())

        self.goto_input = TextInput(
            hint_text="Semaine ou date DD/MM/YYYY",
            multiline=False,
            size_hint=(None, None),
            width=260,
            height=30,
        )
        self.goto_input.bind(on_text_validate=self._on_goto_input)

        self.header.add_widget(self.titre_semaine)
        self.header.add_widget(self.bouton_aujourdhui)
        self.header.add_widget(self.goto_input)
        self.layout.add_widget(self.header)

        self.carousel = CarouselWidget()
        self.carousel.bind(index=self._on_carousel_index)
        self.layout.add_widget(self.carousel)
        self._refresh_entete()

        # Le logiciel peut rester ouvert après minuit
        self._jour = datetime.date.today()
        Clock.schedule_interval(self._verifier_changement_de_jour, 60)

    def go_date(self, date=None):
        self.layout.remove_widget(self.carousel)
        self.carousel = CarouselWidget(date)
        self.carousel.bind(index=self._on_carousel_index)
        self.layout.add_widget(self.carousel)
        # Les réglages (alternance, jours affichés) ont pu changer (go_agenda)
        self._refresh_entete()

    def _on_goto_input(self, instance):
        text = instance.text.strip()
        if not text:
            return
        try:
            if text.isdigit():
                year = datetime.date.today().year
                date = datetime.date.fromisocalendar(year, int(text), 1)
            else:
                # Try new format DD/MM/YYYY first, then legacy YYYY-MM-DD
                try:
                    date = datetime.datetime.strptime(text, "%d/%m/%Y").date()
                except ValueError:
                    date = datetime.datetime.strptime(text, "%Y-%m-%d").date()
            self.go_date(date)
        except ValueError:
            pass
        instance.text = ""

    def _refresh_entete(self, *args):
        jour = self.carousel.date
        aujourdhui = datetime.date.today()
        start_day = start_day_configure()
        debut = debut_de_semaine(jour, start_day)
        # Le lundi de la grille donne le numéro et la lettre, même si la
        # semaine affichée commence un autre jour.
        lundi = debut + datetime.timedelta(days=-start_day % 7)
        jours = list(
            BaseGrid._get_week_days(jour, start_day, BaseGrid.get_days_to_show())
        )
        self.titre_semaine.text = titre_semaine(
            lundi, jours, ecart_en_semaines(jour, aujourdhui, start_day)
        )
        hors_accueil = ecart_en_semaines(jour, date_accueil(aujourdhui), start_day) != 0
        self.bouton_aujourdhui.opacity = 1 if hors_accueil else 0
        self.bouton_aujourdhui.disabled = not hors_accueil

    def _on_carousel_index(self, *args):
        # Wait a tick so CarouselWidget.on_index updates its .date first
        Clock.schedule_once(lambda dt: self._refresh_entete(), 0)

    def _verifier_changement_de_jour(self, *args):
        aujourdhui = datetime.date.today()
        if aujourdhui == self._jour:
            return
        self._jour = aujourdhui
        for grille in self.carousel.slides:
            for jour in grille.children:
                jour.aujourdhui = jour.date == aujourdhui
        self._refresh_entete()
