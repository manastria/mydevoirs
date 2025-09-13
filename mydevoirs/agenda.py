import datetime
import itertools
from typing import List

from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from pony.orm import db_session
from kivy.clock import Clock

from mydevoirs.constants import SEMAINE
from mydevoirs.database import db
from mydevoirs.itemwidget import ItemWidget
from mydevoirs.matieredropdown import MatiereDropdown
from mydevoirs.utils import get_config


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

    def __init__(self, date, **kwargs):
        self.date = date  # need in nice_date
        super().__init__(**kwargs)

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
        semaine = self.date.isocalendar()[1]
        return self.date.strftime("%A %d %B %Y") + f" (sem. {semaine})"

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
        getcfg = get_config("agenda", "start_day", str, "lundi")
        start_day = SEMAINE.index(getcfg)

        for d in self.get_week_days(days_to_show, start_day):
            self.add_widget(JourWidget(d))


class CarouselWidget(Carousel):
    # def on_slides(self, *args):
    #     pass

    def __init__(self, day=None):
        self._removing = False
        self._init = True
        self.date = day or datetime.date.today()

        # adjust the week
        if (
            not day
            and self.date.weekday() in (5, 6)
            and get_config("agenda", "auto_next_week", bool, False)
        ):
            self.date = self.date + datetime.timedelta(days=3)

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

        # Header with current week number + search input on the same line
        self.header = BoxLayout(orientation="horizontal", size_hint_y=None, height=30, spacing=5)

        current_week = datetime.date.today().isocalendar()[1]
        self.week_label = Label(text="", size_hint_x=None)
        # Adjust label width to fit its content
        self.week_label.bind(texture_size=lambda inst, val: setattr(inst, "width", val[0] + 10))

        # Displayed week (from the visible agenda week)
        self.display_week_label = Label(text="", size_hint_x=None)
        self.display_week_label.bind(texture_size=lambda inst, val: setattr(inst, "width", val[0] + 10))

        self.goto_input = TextInput(
            hint_text="Semaine ou date DD/MM/YYYY",
            multiline=False,
            size_hint_y=None,
            height=30,
        )
        self.goto_input.bind(on_text_validate=self._on_goto_input)

        self.header.add_widget(self.week_label)
        self.header.add_widget(self.display_week_label)
        self.header.add_widget(self.goto_input)
        self.layout.add_widget(self.header)

        self.carousel = CarouselWidget()
        self.carousel.bind(index=self._on_carousel_index)
        self.layout.add_widget(self.carousel)
        # Initialize displayed week label according to current carousel
        self._refresh_display_week()
        # Initialize current (today) week label with A/B info
        self.week_label.text = self._format_week_label(current_week)

    def go_date(self, date=None):
        self.layout.remove_widget(self.carousel)
        self.carousel = CarouselWidget(date)
        self.carousel.bind(index=self._on_carousel_index)
        self.layout.add_widget(self.carousel)
        self._refresh_display_week()

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

    # --- internal helpers for week label syncing ---
    @staticmethod
    def _format_week_label(week_number: int) -> str:
        return f"Sem. {week_number} (A)" if week_number % 2 == 1 else f"Sem. {week_number} (B)"

    def _refresh_display_week(self, *args):
        try:
            wk = self.carousel.date.isocalendar()[1]
            self.display_week_label.text = self._format_week_label(wk)
        except Exception:
            # Best-effort; avoid hard failures in UI building
            self.display_week_label.text = ""

    def _on_carousel_index(self, *args):
        # Wait a tick so CarouselWidget.on_index updates its .date first
        Clock.schedule_once(lambda dt: self._refresh_display_week(), 0)
