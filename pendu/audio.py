"""Sons et vibrations, désactivables dans les paramètres."""
from kivy.core.audio import SoundLoader
from kivy.logger import Logger
from kivy.utils import platform

from .config import sound


class Audio:
    def __init__(self, settings: dict):
        self.settings = settings
        self._cache = {}

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
            from plyer import vibrator
            vibrator.vibrate(ms / 1000)
        except Exception as exc:  # plyer absent ou permission refusée
            Logger.debug(f"Pendu: vibration indisponible ({exc})")
