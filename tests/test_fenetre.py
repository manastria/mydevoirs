import pytest
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.event import EventDispatcher
from kivy.properties import ListProperty

import mydevoirs.fenetre
from mydevoirs.fenetre import (
    TailleFenetre,
    est_maximisee,
    taille_a_appliquer,
)
from mydevoirs.settings import DEFAULT_SETTINGS

ZONE = (1366, 728)  # portable 1366×768, barre des tâches déduite


@pytest.mark.parametrize(
    "taille, maximisee, zone, attendu",
    [
        ((1200, 700), False, ZONE, (1200, 700)),  # tient dans l'écran
        ((1200, 800), False, ZONE, None),  # trop haute : reste maximisée
        ((1400, 600), False, ZONE, None),  # trop large
        ((1366, 728), False, ZONE, (1366, 728)),  # juste à la taille
        ((1200, 700), True, ZONE, None),  # était maximisée
        ((1200, 800), False, None, (1200, 800)),  # écran non mesuré
        ((1200, 800), True, None, None),
    ],
)
def test_taille_a_appliquer(taille, maximisee, zone, attendu):
    assert taille_a_appliquer(taille, maximisee, zone) == attendu


def test_est_maximisee():
    assert est_maximisee((1366, 728), ZONE)
    assert est_maximisee((1365, 729), ZONE)  # tolérance
    assert not est_maximisee((1200, 700), ZONE)
    assert not est_maximisee((1366, 728), None)


class FausseFenetre(EventDispatcher):
    """Simule le système : maximize() donne à la fenêtre la zone utile."""

    system_size = ListProperty([800, 600])

    def __init__(self, zone=ZONE, obeit=True):
        super().__init__()
        self.zone = zone
        self.obeit = obeit
        self.appels = []

    def maximize(self):
        self.appels.append("maximize")
        if self.obeit:
            self.system_size = list(self.zone)

    def restore(self):
        self.appels.append("restore")


def config(largeur, hauteur, maximisee):
    c = ConfigParser()
    c.setdefaults("fenetre", DEFAULT_SETTINGS["fenetre"])
    c.set("fenetre", "largeur", largeur)
    c.set("fenetre", "hauteur", hauteur)
    c.set("fenetre", "maximisee", maximisee)
    return c


def lancer(fenetre, cfg):
    tf = TailleFenetre(fenetre, cfg)
    tf.appliquer()
    Clock.tick()  # maximize() est appelé au tour suivant
    return tf


def test_defaut_premier_lancement():
    c = ConfigParser()
    c.setdefaults("fenetre", DEFAULT_SETTINGS["fenetre"])
    w = FausseFenetre()
    tf = lancer(w, c)
    assert tf.zone_utile == ZONE
    assert w.appels == ["maximize"]
    assert tuple(w.system_size) == ZONE


def test_restaure_une_taille_qui_tient():
    w = FausseFenetre()
    tf = lancer(w, config(1000, 600, 0))
    assert tf.zone_utile == ZONE
    assert w.appels == ["maximize", "restore"]
    assert tuple(w.system_size) == (1000, 600)


def test_taille_trop_grande_reste_maximisee():
    w = FausseFenetre()
    lancer(w, config(1200, 800, 0))
    assert w.appels == ["maximize"]
    assert tuple(w.system_size) == ZONE


def test_maximize_ignore_par_le_systeme(monkeypatch):
    monkeypatch.setattr(mydevoirs.fenetre, "DELAI_MESURE", 0)
    w = FausseFenetre(obeit=False)
    tf = lancer(w, config(1000, 600, 0))
    Clock.tick()  # délai de secours écoulé
    assert tf.zone_utile is None
    assert tuple(w.system_size) == (1000, 600)


def test_enregistrer_non_maximisee():
    w = FausseFenetre()
    c = config(1000, 600, 0)
    tf = lancer(w, c)
    w.system_size = [1100, 650]  # l'utilisateur redimensionne
    tf.enregistrer()
    assert c.getint("fenetre", "largeur") == 1100
    assert c.getint("fenetre", "hauteur") == 650
    assert c.getint("fenetre", "maximisee") == 0


def test_enregistrer_maximisee_garde_la_taille_de_sortie():
    w = FausseFenetre(zone=(1908, 999))
    c = config(1200, 800, 1)
    tf = lancer(w, c)
    tf.enregistrer()
    assert c.getint("fenetre", "maximisee") == 1
    assert (c.getint("fenetre", "largeur"), c.getint("fenetre", "hauteur")) == (
        1200,
        800,
    )


def test_enregistrer_maximisee_ramene_une_taille_trop_grande():
    w = FausseFenetre()
    c = config(3000, 2000, 0)
    tf = lancer(w, c)
    tf.enregistrer()
    assert c.getint("fenetre", "maximisee") == 1
    assert (c.getint("fenetre", "largeur"), c.getint("fenetre", "hauteur")) == ZONE
