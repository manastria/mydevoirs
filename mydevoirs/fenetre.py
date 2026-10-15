"""
Taille de la fenêtre au lancement.

Kivy ne donne pas la taille de l'écran. On maximise donc la fenêtre : la taille
que lui donne le système est la zone utile de l'écran (barre des tâches
exclue). Si la taille enregistrée à la dernière fermeture y tient, on la
restaure ; sinon la fenêtre reste maximisée.

Toutes les tailles sont lues et écrites avec `Window.system_size` : sous
Windows, `Window.size` se lit en pixels physiques mais s'écrit en pixels
logiques, ce qui fausserait la taille dès que l'affichage est mis à l'échelle.
"""
from typing import Optional, Tuple

from kivy.clock import Clock

Taille = Tuple[int, int]

TAILLE_PAR_DEFAUT = (1200, 800)

# Au-delà, on renonce à mesurer l'écran (maximisation ignorée par le système)
DELAI_MESURE = 1.0

# Écart toléré, en pixels, pour considérer qu'une fenêtre est maximisée
TOLERANCE = 2


def taille_a_appliquer(
    taille: Taille, maximisee: bool, zone_utile: Optional[Taille]
) -> Optional[Taille]:
    """Taille à donner à la fenêtre, ou None pour la laisser maximisée."""
    if maximisee:
        return None
    if zone_utile is None:
        return taille
    if taille[0] <= zone_utile[0] and taille[1] <= zone_utile[1]:
        return taille
    return None


def est_maximisee(taille: Taille, zone_utile: Optional[Taille]) -> bool:
    if zone_utile is None:
        return False
    return all(abs(t - z) <= TOLERANCE for t, z in zip(taille, zone_utile))


class TailleFenetre:
    """Applique la taille enregistrée au lancement et l'enregistre à la fermeture."""

    def __init__(self, window, config):
        self.window = window
        self.config = config
        self.zone_utile: Optional[Taille] = None
        self._avant: Optional[Taille] = None
        self._secours = None

    def taille_enregistree(self) -> Taille:
        return (
            self.config.getdefaultint("fenetre", "largeur", TAILLE_PAR_DEFAUT[0]),
            self.config.getdefaultint("fenetre", "hauteur", TAILLE_PAR_DEFAUT[1]),
        )

    def maximisee_enregistree(self) -> bool:
        return bool(self.config.getdefaultint("fenetre", "maximisee", 1))

    def appliquer(self):
        # C'est la taille que retrouvera l'utilisateur en quittant le mode maximisé
        self.window.system_size = self.taille_enregistree()
        # Au tour suivant, une fois la taille ci-dessus appliquée par Kivy :
        # sinon ce redimensionnement annulerait la maximisation.
        Clock.schedule_once(self._maximiser, 0)

    def _maximiser(self, dt):
        self._avant = tuple(self.window.system_size)
        self.window.bind(system_size=self._on_system_size)
        # Programmé ici et non dans appliquer() : Kivy compte le délai depuis
        # la dernière image, qui peut dater de plus d'une seconde au démarrage.
        self._secours = Clock.schedule_once(
            lambda dt: self._fin_mesure(None), DELAI_MESURE
        )
        self.window.maximize()

    def _on_system_size(self, window, taille):
        if tuple(taille) != self._avant:
            self._fin_mesure(tuple(taille))

    def _fin_mesure(self, zone_utile: Optional[Taille]):
        self.window.unbind(system_size=self._on_system_size)
        self._secours.cancel()
        self.zone_utile = zone_utile
        taille = taille_a_appliquer(
            self.taille_enregistree(), self.maximisee_enregistree(), zone_utile
        )
        if taille:
            self.window.restore()
            self.window.system_size = taille

    def enregistrer(self):
        taille = tuple(self.window.system_size)
        maximisee = est_maximisee(taille, self.zone_utile)
        if maximisee:
            # Garder la taille de sortie du mode maximisé, ramenée à l'écran
            taille = tuple(
                min(t, z) for t, z in zip(self.taille_enregistree(), self.zone_utile)
            )
        self.config.set("fenetre", "largeur", taille[0])
        self.config.set("fenetre", "hauteur", taille[1])
        self.config.set("fenetre", "maximisee", int(maximisee))
        self.config.write()
