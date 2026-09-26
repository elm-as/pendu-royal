
import random

from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class LetterShuffle():
    def __init__(self, event_manager,**kwargs):
        super().__init__(**kwargs)

        self.event_manager = event_manager
        self._letter_shuffle = {
            "event_name": "letter_shuffle",
            "type": "penality",
            "rarity": "rare",
            "description": "Le clavier change temporairement de disposition.",
            "activate": None
        }

    def _on_letter_shuffle(self, dt):
            
        print("[_on_letter_shuffle]")
        Clock.schedule_once(self._clean_keyboard, 0)

    def _clean_keyboard(self, dt):
        """This methode used in the _on_letter_shuffle methohde"""

        print("[_clean_keyboard]")
        if self.event_manager.copy_of_keyboard_buttons != []:
            self.event_manager.button = random.choice(self.event_manager.copy_of_keyboard_buttons)
            self.event_manager.button.text = ""
            self.event_manager.copy_of_keyboard_buttons.remove(self.event_manager.button)
            Clock.schedule_once(self._clean_keyboard, 0.02)
        else:
            self.event_manager.copy_of_keyboard_buttons = self.event_manager.keyboard_buttons.copy()
            self.event_manager.copy_of_letters_of_keyboard_buttons = self.event_manager.letters_of_keyboard_buttons.copy()
            self.event_manager.displayed_buttons = []
            Clock.schedule_once(self._fixe_the_keyboard, 0.02)

    def _fixe_the_keyboard(self, dt):
        """This methode used in the _on_letter_shuffle methohde"""

        print("[_fixe_the_keyboard]")
        if self.event_manager.copy_of_keyboard_buttons == []:
            self.event_manager.copy_of_keyboard_buttons = self.event_manager.keyboard_buttons.copy()
            self.event_manager.copy_of_letters_of_keyboard_buttons = self.event_manager.letters_of_keyboard_buttons.copy()
            self.event_manager.button_index = 0
            self._letter_shuffle_animation(displayed_buttons=self.event_manager.displayed_buttons, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON2"], end=True)
            self.event_manager.main.stop_timer = False
            self.event_manager.main.is_keyboard_closed = False
            Clock.schedule_once(self.event_manager.main.timer, 0)
        else:
            self.event_manager.button = random.choice(self.event_manager.copy_of_keyboard_buttons)
            self.event_manager.letter = random.choice(self.event_manager.copy_of_letters_of_keyboard_buttons)
            self.event_manager.button.text = self.event_manager.letter
            self.event_manager.displayed_buttons.append(self.event_manager.button)
            self._letter_shuffle_animation(displayed_buttons=self.event_manager.displayed_buttons, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON2"])
            self.event_manager.copy_of_keyboard_buttons.remove(self.event_manager.button)
            self.event_manager.copy_of_letters_of_keyboard_buttons.remove(self.event_manager.letter)
            Clock.schedule_once(self._fixe_the_keyboard, 0.04)

    def _letter_shuffle_animation(self, displayed_buttons, color, end=False):
        if end:
            self.event_manager.last_button = displayed_buttons[-1]
            self.event_manager.last_button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])
            return
        self.event_manager.button = displayed_buttons[-1]
        self.event_manager.button.bg_color = get_color_from_hex(color)
        if len(displayed_buttons) > 1:
            self.event_manager.before_button = self.event_manager.displayed_buttons[-2]
            self.event_manager.before_button.bg_color = get_color_from_hex(self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])

    def _reset_keyboard(self, dt):
    
        print("[_reset_keyboard]")
        if self.event_manager.copy_of_keyboard_buttons == []:
            self.event_manager.copy_of_keyboard_buttons = self.event_manager.keyboard_buttons.copy()
            self.event_manager.copy_of_letters_of_keyboard_buttons = self.event_manager.letters_of_keyboard_buttons.copy()
            self._letter_shuffle_animation(displayed_buttons=self.event_manager.displayed_buttons, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"], end=True)
            self.event_manager.main.stop_timer = False
            self.event_manager.locked = False
            self.event_manager.main.is_keyboard_closed = False
            Clock.schedule_once(self.event_manager.main.timer, 1)
        else:
            self.event_manager.button = self.event_manager.copy_of_keyboard_buttons[0]
            self.event_manager.button.text = self.event_manager.copy_of_letters_of_keyboard_buttons[0]
            self.event_manager.displayed_buttons.append(self.event_manager.button)
            self._letter_shuffle_animation(displayed_buttons=self.event_manager.displayed_buttons, color=self.event_manager.COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
            self.event_manager.copy_of_keyboard_buttons.remove(self.event_manager.copy_of_keyboard_buttons[0])
            self.event_manager.copy_of_letters_of_keyboard_buttons.remove(self.event_manager.copy_of_letters_of_keyboard_buttons[0])
            Clock.schedule_once(self._reset_keyboard, 0.04)