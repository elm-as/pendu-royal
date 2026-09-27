"""Sons et vibrations, désactivables dans les paramètres."""
from kivy.core.audio import SoundLoader
from kivy.logger import Logger
from kivy.utils import platform

from .config import sound


class Audio:
    def __init__(self, settings: dict):
        self.settings = settings
        self._cache = {}
        self._vibrator = None

    def play(self, name: str) -> None:
        if not self.settings.get("sound", True):
            return
        if name not in self._cache:
            self._cache[name] = SoundLoader.load(sound(name))
        snd = self._cache[name]
        if snd:
            snd.stop()
            snd.play()

    def vibrate(self, ms: int) -> None:
        if platform != "android" or not self.settings.get("vibration", True):
            return
        try:
            if self._vibrator is None:
                # API Android directe via pyjnius (fourni avec Kivy) : pas besoin de plyer
                from jnius import autoclass
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                context = autoclass("android.content.Context")
                self._vibrator = activity.getSystemService(context.VIBRATOR_SERVICE)
            self._vibrator.vibrate(int(ms))
        except Exception as exc:  # permission refusée, appareil sans vibreur…
            Logger.debug(f"Pendu: vibration indisponible ({exc})")
