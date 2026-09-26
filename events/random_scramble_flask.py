from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class RandomScrambleFlask():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._random_scramble_flask = {
            "event_name": "random_scramble_flask",
            "type": "penality",
            "rarity": "rare",
            "description": "Pendant plusieurs secondes, les lettres sont affichées de manière desordonées (Visuel uniquement).",
            "activate": None
        }

    def _on_random_scramble_flask(self):
            
        print("[_on_random_scramble_flask]")
        self.event_manager.buttons_copy = self.event_manager.main.buttons.copy()
        self.event_manager.button_index2 = 0
        Clock.schedule_once(self._scramble_word_letters, 0)

    def _scramble_word_letters(self, dt):
    
        print("[_scramble_word_letters]")
        if self.event_manager.buttons_copy == []:
            self.event_manager.word_letters = self.event_manager._get_word_letters()
            self.event_manager.buttons_copy = self.event_manager.main.buttons
            self.event_manager.button = self.event_manager.main.buttons.copy()[-1]
            self.event_manager.mirror_letter._mirror_letter_animation(button=self.event_manager.button, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON2"], end=True)
            self.event_manager.main.stop_timer = False
            self.event_manager.locked = True
            self.event_manager.main.is_keyboard_closed = False
            return Clock.schedule_once(self.event_manager.main.timer, 1)
        else:
            self.event_manager.button = self.event_manager.buttons_copy[0]
            if self.event_manager.word_letters[0] in self.event_manager.main.letter_checked:
                self.event_manager.button.text = self.event_manager.word_letters[0]
            else:
                self.event_manager.button.text = "?"
            self.event_manager.button.id = self.event_manager.word_letters[0]
            self.event_manager.mirror_letter._mirror_letter_animation(button=self.event_manager.button, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON2"])
            self.event_manager.buttons_copy = self.event_manager.buttons_copy[1:]
            self.event_manager.word_letters = self.event_manager.word_letters[1:]
            Clock.schedule_once(self._scramble_word_letters, 0.1)