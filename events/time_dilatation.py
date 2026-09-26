from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class TimeDilatation():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._time_dilatation = {
            "event_name": "time_dilatation",
            "type": "bonus",
            "rarity": "epic",
            "description": "Le temps s'coule 2X moins vite jusqu'à a fin du tour",
            "activate": None
        }

    def _on_time_dilatation(self):
        self.event_manager.main.time_step = 2
        self.event_manager.main.stop_timer = False
        self.event_manager.main.is_keyboard_closed = False
        return Clock.schedule_once(self.event_manager.main.timer, 1)