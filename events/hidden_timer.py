from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class HiddenTimer():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._hidden_timer = {
            "event_name": "hidden_timer",
            "type": "penality",
            "rarity": "rare",
            "description": "Le timer devient invisible",
            "activate": None
        }

    def _on_hidden_timer(self):
        self.event_manager.main.is_hidden_timer = True
        self.event_manager.main.stop_timer = False
        self.event_manager.main.is_keyboard_closed = False
        return Clock.schedule_once(self.event_manager.main.timer, 1)