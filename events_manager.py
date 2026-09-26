import random

from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.utils import get_color_from_hex

from events.cold_round import ColdRound
from events.double_or_nothing import DoubleOrNothing
from events.gold_run import GoldRun
from events.hidden_timer import HiddenTimer
from events.letter_shuffle import LetterShuffle
from events.mirror_letter import MirrorLetter
from events.random_scramble_flask import RandomScrambleFlask
from events.second_chance_save import SecondChanceSave
from events.taxe_event import TaxeEvent
from events.time_dilatation import TimeDilatation
from events.time_pressure import TimePressure

class EventsManager():
    """Only used for the game and not other where"""
    def __init__(self, keyboard, displayer, timer, main, COLORS_PALETTE, **kwargs):
        super().__init__(**kwargs)

        self.main = main
        self.displayer = displayer
        self.COLORS_PALETTE = COLORS_PALETTE
        self.keyboard_buttons = [
            keyboard.ids.a0_button,
            keyboard.ids.a1_button,
            keyboard.ids.a2_button,
            keyboard.ids.e0_button,
            keyboard.ids.e1_button,
            keyboard.ids.e2_button,
            keyboard.ids.u0_button,
            keyboard.ids.i0_button,
            keyboard.ids.i1_button,
            keyboard.ids.o0_button,
            keyboard.ids.a3_button,
            keyboard.ids.z_button,
            keyboard.ids.e3_button,
            keyboard.ids.r_button,
            keyboard.ids.t_button,
            keyboard.ids.y_button,
            keyboard.ids.u_button,
            keyboard.ids.i2_button,
            keyboard.ids.o1_button,
            keyboard.ids.p_button,
            keyboard.ids.q_button,
            keyboard.ids.s_button,
            keyboard.ids.d_button,
            keyboard.ids.f_button,
            keyboard.ids.g_button,
            keyboard.ids.h_button,
            keyboard.ids.j_button,
            keyboard.ids.k_button,
            keyboard.ids.l_button,
            keyboard.ids.m_button,
            keyboard.ids.w_button,
            keyboard.ids.x_button,
            keyboard.ids.c_button,
            keyboard.ids.v_button,
            keyboard.ids.b_button,
            keyboard.ids.n_button
        ]

        self._events_check_time = {
            "noob": {
                "end_turn": None
            },
            "medium": {
                "end_turn": None
            },
            "hard": {
                "early_turn": None,
                "mid_turn": None,
                "end_turn": None
            }
        }
        self.copy_of_keyboard_buttons = self.keyboard_buttons.copy()
        self.letters_of_keyboard_buttons = ['à', 'â', 'ä', 'ê', 'é', 'è', 'û', 'ï', 'î', 'ô', 'a', 'z', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'q', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'w', 'x', 'c', 'v', 'b', 'n']
        self.copy_of_letters_of_keyboard_buttons = self.letters_of_keyboard_buttons.copy()
        self.locked = False

        self._events_list = ["mirror_letter", "letter_shuffle", "random_scramble_flask", "time_dilatation", "cold_round", "hidden_timer", "time_pressure"]
        self._early_turn_events = ["mirror_letter", "letter_shuffle", "random_scramble_flask", "time_dilatation", "hidden_timer", "time_pressure"]
        self.mid_turn_events = ["mirror_letter", "letter_shuffle", "random_scramble_flask", "time_dilatation", "hidden_timer", "time_pressure"]
        self._end_turn_events = ["mirror_letter", "letter_shuffle", "random_scramble_flask", "time_dilatation", "hidden_timer", "time_pressure"]
        self.current_event = []
        self.event_information_backup = []
        self.break_time:list[int|int] = []

        self.cold_roud = ColdRound(event_manager=self)
        self.double_or_nothing = DoubleOrNothing(event_manager=self)
        self.gold_run = GoldRun(event_manager=self)
        self.hidden_timer = HiddenTimer(event_manager=self)
        self.letter_shuffle = LetterShuffle(event_manager=self)
        self.mirror_letter = MirrorLetter(event_manager=self)
        self.random_scramble_flask = RandomScrambleFlask(event_manager=self)
        self.second_chance_save = SecondChanceSave(event_manager=self)
        self.taxe_event = TaxeEvent
        self.time_dilatation = TimeDilatation(event_manager=self)
        self.time_pressure = TimePressure(event_manager=self)
        

        self._available_events = ["mirror_letter", "time_dilatation", "hidden_timer", "letter_shuffle", "random_scramble_flask", "time_pressure"]

    def get_event_information(self, event_name:str, key:str)-> str:
        """Give the event description"""

        print("[get_event_information]")
        if event_name in self._events_list:
            return self._get_event_key_value(event_name, key=key)
        else:
            raise AttributeError("Event not exist")
        
    def activate_event(self, event_name:str):
        """Activate the event"""

        print("[activate_event]")
        if event_name in self._events_list:
            return self._get_event_key_value(event_name, key="activate")
        else:
            raise AttributeError("Event not exist")
        
    def _get_event_key_value(self, event_name, key):

        print("[_get_event_key_value]")
        if event_name == "mirror_letter":
            if key == "activate":
                self.current_event.append(["mirror_letter", 10])
                self.word_letters = list(self.main.word_to_find)
                self.word_letters.reverse()
                self.buttons_copy = self.main.buttons.copy()
                self.locked = True
                Clock.schedule_once(lambda dt:self.mirror_letter._erase_word(event=event_name), 0)
            else:
                return self.mirror_letter._mirror_letter[key]
        elif event_name == "random_scramble_flask":
            if key == "activate":
                self.current_event.append(["random_scramble_flask", 15])
                self.word_letters = list(self.main.word_to_find)
                random.shuffle(self.word_letters)
                self.copy_of_word_letters = self.word_letters.copy()
                self.buttons_copy = self.main.buttons.copy()
                self.locked = True
                Clock.schedule_once(lambda dt:self.mirror_letter._erase_word(event=event_name), 0)
            else:
                return self.random_scramble_flask._random_scramble_flask[key]
        elif event_name == "letter_shuffle":
            if key == "activate":
                self.locked = True
                self.current_event.append(["letter_shuffle", 15])
                return Clock.schedule_once(self.letter_shuffle._on_letter_shuffle, 0)
            else:
                return self.letter_shuffle._letter_shuffle[key]
        elif event_name == "cold_round":
            if key == "activate":
                self.current_event.append(["mirror_letter", 10])
                self.locked = True
                return self._on_cold_round()
            else:
                return self.cold_roud._cold_round[key]
        elif event_name == "time_dilatation":
            if key == "activate":
                self.current_event.append(["time_dilatation", 10])
                self.locked = True
                return self.time_dilatation._on_time_dilatation()
            else:
                return self.time_dilatation._time_dilatation[key]
        elif event_name == "time_pressure":
            if key == "activate":
                self.current_event.append(["time_pressure", 10])
                self.locked = True
                return self.time_pressure._on_time_pressure()
            else:
                return self.time_pressure._time_pressure[key]
        elif event_name == "hidden_timer":
            if key == "activate":
                self.current_event.append(["hidden_timer", 10])
                self.locked = True
                return self.hidden_timer._on_hidden_timer()
            else:
                return self.hidden_timer._hidden_timer[key]

    def _get_word_letters(self):

        print("[_get_word_letters]")
        self.letters = []
        for button in self.main.buttons:
            self.letters.append(button.text)
        return self.letters
    
    def _on_cold_round(self):

        print("[_on_cold_round]")

    def progress(self):

        print("[progress]")
        i = 0
        for liste in self.current_event:
            if liste[0] == "letter_shuffle":
                if liste[1] == 0:
                    self.current_event.remove(liste)
                    self.main.is_keyboard_closed = True
                    self._close_event(event="letter_shuffle")
                else:
                    self.current_event[i][1] -= 1
            elif liste[0] == "mirror_letter":
                if liste[1] == 0:
                    self.current_event.remove(liste)
                    self.main.is_keyboard_closed = True
                    self._close_event(event="mirror_letter")
                else:
                    self.current_event[i][1] -= 1
            elif liste[0] == "random_scramble_flask":
                if liste[1] == 0:
                    self.current_event.remove(liste)
                    self.main.is_keyboard_closed = True
                    self._close_event(event="random_scramble_flask")
                else:
                    self.current_event[i][1] -= 1
            elif liste[0] == "time_dilatation":
                if liste[1] == 0:
                    self.current_event.remove(liste)
                    self.main.is_keyboard_closed = True
                    self._close_event(event="time_dilatation")
                else:
                    self.current_event[i][1] -= 1
            elif liste[0] == "time_pressure":
                if liste[1] == 0:
                    self.current_event.remove(liste)
                    self.main.is_keyboard_closed = True
                    self._close_event(event="time_pressure")
                else:
                    self.current_event[i][1] -= 1
            elif liste[0] == "hidden_timer":
                if liste[1] == 0:
                    self.current_event.remove(liste)
                    self.main.is_keyboard_closed = True
                    self._close_event(event="hidden_timer")
                else:
                    self.current_event[i][1] -= 1
            i += 1

    def _close_event(self, event:str):
        """End the event choosed"""

        print("[_close_event]")
        self.main.is_keyboard_closed = True
        self.main.stop_timer = True
        if event == "letter_shuffle":
            self.event_information = self.get_event_information(event_name=event, key="description")
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0)
        elif event == "mirror_letter":
            self.word_letters = self.main.word_to_find
            self.buttons_copy = self.main.buttons.copy()
            self.event_information = self.get_event_information(event_name=event, key="description")
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0)
        elif event == "random_scramble_flask":
            self.word_letters = self.copy_of_word_letters
            self.buttons_copy = self.main.buttons.copy()
            self.event_information = self.get_event_information(event_name=event, key="description")
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0)
        elif event == "time_dilatation":
            self.event_information = self.get_event_information(event_name=event, key="description")
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0)
        elif event == "time_pressure":
            self.event_information = self.get_event_information(event_name=event, key="description")
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0)
        elif event == "hidden_timer":
            self.event_information = self.get_event_information(event_name=event, key="description")
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0)

    def restore_event_dommage(self, event:str):
        if event == "letter_shuffle":
            self.displayed_buttons = []
            self.copy_of_letters_of_keyboard_buttons = self.letters_of_keyboard_buttons.copy()
            self.copy_of_keyboard_buttons = self.keyboard_buttons.copy()
            Clock.schedule_once(self.letter_shuffle._reset_keyboard, 0)
        elif event =="mirror_letter":
            self.buttons_copy = self.main.buttons.copy()
            self.word_letters = self.main.word_to_find
            Clock.schedule_once(self.mirror_letter._restore_word_letter, 0)
        elif event =="random_scramble_flask":
            self.buttons_copy = self.main.buttons.copy()
            self.word_letters = self.main.word_to_find
            Clock.schedule_once(self.mirror_letter._restore_word_letter, 0)
        elif event =="time_dilatation":
            self.main.time_step = 1#self.main.default_time_step
            self.locked = False
            self.main.stop_timer = False
            self.main.is_keyboard_closed = False
            return
        elif event == "time_pressure":
            self.main.time_step = 1#self.main.default_time_step
            self.locked = False
            self.main.stop_timer = False
            self.main.is_keyboard_closed = False
            return Clock.schedule_once(self.main.timer, 0)
        elif event == "hidden_timer":
            self.main.is_hidden_timer = False
            self.locked = False
            self.main.stop_timer = False
            self.main.is_keyboard_closed = False
            return


    def add_event(self, event:str):

        print("[add_event]")
        self.main.stop_timer = True
        self.main.is_keyboard_closed = True
        self.event_badge = Image(pos_hint={"x":0.7, "center_y":0.5}, size_hint=(0.35, 1), source=self.main.get_image_path(f"{event}.png"))
        self.main.ids.event_displayer.add_widget(self.event_badge)
        Clock.schedule_once(lambda dt:self._event_animation(event=event), 0)

    def _event_animation(self, event:str):

        print("[_event_animation]")
        Animation(pos_hint={"x":0}, duration=0.4).start(self.event_badge)
        self.event_information = self.get_event_information(event_name=event, key="description")
        Clock.schedule_once(lambda dt:self._add_event_information_box(event=event), 0.5)

    def _add_event_information_box(self, event:str):

        print("[_add_event_information_box]")
        self.main.event_information_box = self.main.craft_event_information_box()
        self.event_information_backup.append(self.main.event_information_box)
        self.displayer.add_widget(self.event_information_backup[0])
        Clock.schedule_once(lambda dt:self._display_event_information(event=event), 0)

    def _display_event_information(self, event:str):

        if self.event_information == "":
            self.activate_event(event_name=event)
        else:
            self.event_information_backup[0].event_information_label.text += self.event_information[0]
            self.event_information = self.event_information[1:]
            Clock.schedule_once(lambda dt:self._display_event_information(event=event), 0.015)

    def _delete_event_information(self, event:str):

        if self.event_information == "":
            if self.event_badge in self.displayer.children:
                self.displayer.remove_widget(self.event_badge)
            for widget in self.displayer.children:
                self.displayer.remove_widget(widget)
            self.restore_event_dommage(event=event)
        else:
            self.event_information_backup[0].event_information_label.text = self.event_information[:-1]
            self.event_information = self.event_information[:-1]
            Clock.schedule_once(lambda dt:self._delete_event_information(event=event), 0.015)

    def check_event_window(self, timer, level):
        
        print(f"[check_event_window][self.locked == {self.locked}]")
        if self.locked:
            return
        if self._events_check_time[level]["early_turn"] == None:
            # Not event can be activate in the first turn
            return
        if level == "hard":
            if timer == self._events_check_time["hard"]["early_turn"]:
                self._event_spawn_roll(moment="early_turn")
            elif timer == self._events_check_time["hard"]["mid_turn"]:
                self._event_spawn_roll(moment="mid_turn")
            elif timer == self._events_check_time["hard"]["end_turn"]:
                self._event_spawn_roll(moment="end_turn")

    def select_events_time(self):
        """Select a time where _event_spaxn_roll will be activated"""

        print("[select_events_time]")
        self._events_check_time["hard"]["early_turn"] = random.randint(25, 30)
        self._events_check_time["hard"]["mid_turn"] = random.randint(15, 20)
        self._events_check_time["hard"]["end_turn"] = random.randint(5, 10)

    def _event_spawn_roll(self, moment:str):

        print("[event_spawn_roll]")
        if self._event_spawn(moment=moment):
            self.event_rarity = self._roll_rarity()
            self.event = self.trigger_event(type=random.choice(["penality", "bonus"]), rarity=self.event_rarity)
            print(self.event)
            if self.event in self._available_events:
                # Exlude events that are not been implemented yet
                self.add_event(event=self.event)

    def _event_spawn(self, moment:str):
        if moment == "early_turn" and random.randint(0, 100) <= 50:
            return True
        elif moment == "mid_turn" and random.randint(0, 100) <= 50:
            return True
        elif moment == "end_turn" and random.randint(0, 100) <= 50:
            return True
    
    def _roll_rarity(self):
        if random.randint(0, 100) <= 5:
            self.is_epic_event = True
        else:
            self.is_epic_event = False
        if random.randint(0, 100) <= 30:
            self.is_rare_event = True
        else:
            self.is_rare_event = False
        if self.is_epic_event:
            return "epic"
        else:
            if self.is_rare_event:
                return "rare"
            else:
                return "common"
            
    def trigger_event(self, type:str, rarity:str) -> str:
        """Return the corresponding event name"""

        print(f"[trigger_event][type = {type}, rarity = {rarity}]")
        self.corresponding_events = []
        for event_name in self._events_list:
            if type == self.get_event_information(event_name=event_name, key="type") and rarity == self.get_event_information(event_name=event_name, key="rarity"):
                self.corresponding_events.append(event_name)
        print(f"[corresponding_events={self.corresponding_events}]")
        print(f"[events_list={self._events_list}]")
        if self.corresponding_events != []:
            return random.choice(self.corresponding_events)
