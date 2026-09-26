from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class MirrorLetter():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._mirror_letter = {
            "event_name": "mirror_letter",
            "type": "penality",
            "rarity": "common",
            "description": "Pendant plusieurs secondes, les lettres sont affichées de manière inversées (visuel uniquement).",
            "activate": None,
        }

    def _erase_word(self, event:str):
    
        print("[_erase_word]")
        if self.event_manager.buttons_copy == []:
            if event == "mirror_letter":
                return Clock.schedule_once(self._on_mirror_letter, 0)
            elif event == "random_scramble_flask":
                return self.event_manager.random_scramble_flask._on_random_scramble_flask()
        self.event_manager.button = self.event_manager.buttons_copy[0]
        self.event_manager.button.text = ""
        self.event_manager.button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])
        self.event_manager.buttons_copy = self.event_manager.buttons_copy[1:]
        Clock.schedule_once(lambda dt:self._erase_word(event=event), 0.1)

    def _on_mirror_letter(self, dt):
                
        print("[_on_mirror_letter]")
        self.event_manager.buttons_copy = self.event_manager.main.buttons.copy()
        Clock.schedule_once(self._inverse_word_letters, 0)

    def _inverse_word_letters(self, dt):
        print(f"[_inverse_word_letters][word_letters={self.event_manager.word_letters}]")
        print(f"id={self.event_manager.button.id}")
        if self.event_manager.buttons_copy == []:
            self.event_manager.word_letters = list(self.event_manager.main.copy_of_word_to_find).reverse()
            self.event_manager.buttons_copy = self.event_manager.main.buttons
            self.event_manager.button = self.event_manager.main.buttons.copy()[-1]
            self._mirror_letter_animation(button=self.event_manager.button, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON2"], end=True)
            self.event_manager.main.stop_timer = False
            self.event_manager.locked = True
            self.event_manager.main.is_keyboard_closed = False
            return Clock.schedule_once(self.event_manager.main.timer, 1)
        else:
            self.event_manager.button = self.event_manager.buttons_copy[0]
            self.event_manager.button.text = self.event_manager.word_letters[0]
            if self.event_manager.word_letters[0] in self.event_manager.main.letter_checked:
                self.event_manager.button.text = self.event_manager.word_letters[0]
            else:
                self.event_manager.button.text = "?"
            self.event_manager.button.id = self.event_manager.word_letters[0]
            self._mirror_letter_animation(button=self.event_manager.button, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON2"])
            self.event_manager.buttons_copy = self.event_manager.buttons_copy[1:]
            self.event_manager.word_letters = self.event_manager.word_letters[1:]
            Clock.schedule_once(self._inverse_word_letters, 0.1)

    def _mirror_letter_animation(self, button, color:str, end=False):
        if end:
            if self.event_manager.button.text in self.event_manager.main.letter_checked:
                self.event_manager.button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
            else:
                self.event_manager.button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])
            return
        button.bg_color = get_color_from_hex(color)
        if button != self.event_manager.main.buttons.copy()[0]:
            i = 0
            for btn in self.event_manager.main.buttons.copy():
                if btn == button:
                    self.event_manager.before_button = self.event_manager.main.buttons.copy()[i-1]
                    if self.event_manager.before_button.text in self.event_manager.main.letter_checked:
                        self.event_manager.before_button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
                    else:
                        self.event_manager.before_button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])
                    break
                i += 1

    def _restore_word_letter(self, dt):
    
        print("[_restore_word_letters]")
        if self.event_manager.buttons_copy == []:
            self.event_manager.word_letters = list(self.event_manager.main.copy_of_word_to_find).reverse()
            self.event_manager.buttons_copy = self.event_manager.main.buttons
            self._mirror_letter_animation(button=self.event_manager.button, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"], end=True)
            self.event_manager.main.stop_timer = False
            self.event_manager.locked = False
            self.event_manager.main.is_keyboard_closed = False
            return Clock.schedule_once(self.event_manager.main.timer, 1)
        else:
            self.event_manager.button = self.event_manager.buttons_copy[0]
            self.event_manager.button.text = self.event_manager.word_letters[0]
            if self.event_manager.word_letters[0] in self.event_manager.main.letter_checked:
                self.event_manager.button.text = self.event_manager.word_letters[0]
            else:
                self.event_manager.button.text = "?"
            self.event_manager.button.id = self.event_manager.word_letters[0]
            self._mirror_letter_animation(button=self.event_manager.button, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
            self.event_manager.buttons_copy = self.event_manager.buttons_copy[1:]
            self.event_manager.word_letters = self.event_manager.word_letters[1:]
            Clock.schedule_once(self._restore_word_letter, 0.1)