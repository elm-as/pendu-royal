from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class TimePressure():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._time_pressure = {
            "event_name": "time_pressure",
            "type": "penality",
            "rarity": "epic",
            "description": "Le temps coule 2X plus vite jusqu'à a fin du tour",
            "activate": None
        }

    def _on_time_pressure(self):
        self.event_manager.main.time_step = 0.5
        self.event_manager.main.stop_timer = False
        self.event_manager.main.is_keyboard_closed = False
        return Clock.schedule_once(self.event_manager.main.timer, 1)