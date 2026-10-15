import datetime
import os
import webbrowser
from pathlib import Path

from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.settings import SettingItem, SettingPath, SettingSpacer, SettingString
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy_garden.filebrowser import FileBrowser

from mydevoirs.alternance import (
    lettre_semaine,
    libelles_configures,
    parse_reference,
    reference_pour,
)
from mydevoirs.ouinonpopup import OuiNonPopup

"""
SettingsPath using  Filebrowser instead Filechooser
"""


class SettingFilePath(SettingPath):
    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.filename
        if not value:
            return
        self.new_value = os.path.realpath(value)
        if self.new_value == self.value:
            return

        OuiNonPopup(
            title="Copier le contenu de l'ancienne base de données vers la nouvelle ?",
            on_oui=self._copy_ddb,
            on_non=self._update_value,
        )

    def _copy_ddb(self, *args):
        def write(*args):
            new.write_bytes(old.read_bytes())
            self._update_value()

        old = Path(self.value)
        new = Path(self.new_value)
        if new.exists():
            OuiNonPopup(
                title=f"Confirmez le remplacement du contenu de {str(new)} par {str(old)}",
                on_oui=write,
                on_non=self._dismiss,
            )
        else:
            write()
            self._update_value()

    def _update_value(self, *args):
        self.value = self.new_value

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation="vertical", spacing=5)
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(1, 0.9)
        )

        # create the filechooser
        initial_path = self.value or os.getcwd()

        self.textinput = textinput = FileBrowser(
            path=initial_path, size_hint=(1, 1), dirselect=False, show_hidden=True
        )
        textinput.bind(on_success=self._validate)
        textinput.bind(on_submit=self._validate)
        textinput.bind(on_canceled=self._dismiss)

        # construct the content
        content.add_widget(textinput)
        popup.open()


class SettingCustomConfigFilePath(SettingPath):
    def _validate(self, instance):
        self._dismiss()
        value = self.textinput.filename
        if not value:
            return
        self.new_value = os.path.realpath(value)
        if self.new_value == self.value:
            return

        OuiNonPopup(
            title="Confirmer l'ajout du fichier de configuration  ?",
            on_oui=self._do_yes,
            on_non=self._dismiss,
        )

    def _do_yes(self, *args):
        self.value = self.new_value

    # def _:
    # def write(*args):
    #     new.write_bytes(old.read_bytes())
    #     self._update_value()
    #
    # old = Path(self.value)
    # new = Path(self.new_value)
    # if new.exists():
    #     OuiNonPopup(
    #         title=f"Confirmez le remplacement du contenu de {str(new)} par {str(old)}",
    #         on_oui=write,
    #         on_non=self._dismiss,
    #     )
    # else:
    #     write()
    #     self._update_value()

    def _do_no(self, *args):
        def do_yes(*args):
            self.value = ""

        def do_no(*args):
            pass

        OuiNonPopup(
            title="Déselectionner le fichier de configurtion  ?",
            on_oui=do_yes,
            on_non=do_no,
        )
        self._dismiss()

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation="vertical", spacing=5)
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(1, 0.9)
        )

        # create the filechooser
        initial_path = self.value or os.getcwd()

        self.textinput = textinput = FileBrowser(
            path=initial_path, size_hint=(1, 1), dirselect=False, show_hidden=True
        )
        textinput.bind(on_success=self._validate)
        textinput.bind(on_submit=self._validate)
        textinput.bind(on_canceled=self._do_no)

        # construct the content
        content.add_widget(textinput)
        popup.open()


class SettingLabel(SettingString):
    def on_panel(self, instance, value):
        self.fbind("on_release", self.open_url)

    def open_url(self, *args):
        webbrowser.open_new(self.value)

    def _dismiss(self, *largs):  # pragma: no cover_all
        pass

    def _validate(self, instance):  # pragma: no cover_all
        pass

    def _create_popup(self, instance):  # pragma: no cover_all
        pass


class SettingSemaineCourante(SettingItem):
    """
    Choix de la lettre de la semaine en cours.

    La valeur enregistrée est le lundi de référence (AAAA-MM-JJ) : l'utilisateur
    ne voit et ne choisit que la lettre, la date en est déduite.
    """

    lettre = StringProperty("")
    popup = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        label = Label(text=self.lettre, font_size="15sp")
        self.bind(lettre=label.setter("text"))
        self.add_widget(label)
        self._refresh_lettre()

    def on_panel(self, instance, value):
        if value is None:
            return
        self.fbind("on_release", self._create_popup)
        # les libellés peuvent changer pendant que le panneau est ouvert
        if value.settings:
            value.settings.fbind("on_config_change", self._refresh_lettre)

    def on_value(self, instance, value):
        super().on_value(instance, value)
        self._refresh_lettre()

    def _refresh_lettre(self, *args):
        self.lettre = lettre_semaine(
            datetime.date.today(), parse_reference(self.value), libelles_configures()
        )

    def _set_lettre(self, instance):
        self.value = reference_pour(
            datetime.date.today(), instance.text, libelles_configures()
        ).isoformat()
        self.popup.dismiss()

    def _create_popup(self, instance):
        libelles = libelles_configures()
        content = BoxLayout(orientation="vertical", spacing="5dp")
        self.popup = popup = Popup(
            content=content,
            title=self.title,
            size_hint=(0.8, None),
            height=len(libelles) * dp(55) + dp(150),
        )

        content.add_widget(Widget(size_hint_y=None, height=1))
        for lettre in libelles:
            state = "down" if lettre == self.lettre else "normal"
            btn = ToggleButton(text=lettre, state=state, group=str(self.uid))
            btn.bind(on_release=self._set_lettre)
            content.add_widget(btn)

        content.add_widget(SettingSpacer())
        btn = Button(text="Annuler", size_hint_y=None, height=dp(50))
        btn.bind(on_release=popup.dismiss)
        content.add_widget(btn)

        popup.open()
