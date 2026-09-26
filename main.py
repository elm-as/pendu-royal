import os
import pickle
import random
import json
import time

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, FallOutTransition, WipeTransition, SlideTransition
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.properties import ObjectProperty, ListProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.resources import resource_find
from kivy.graphics import Color, RoundedRectangle
from pathlib import Path
from events_manager import EventsManager

COLORS_PALETTE = {
    "CREATE_ACCOUNT_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913"
        },
    },
    "WELCOME_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "MAIN_BUTTONS": {
                "ON_PRESS": "#A85A29",
                "ON_RELEASE": "#8F4A1B"
            },
        },
        "TEXT": {
            "MAIN_LABEL": "#E5A600"
        }
    },
    "LEVEL_SELECTING_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "EXIT_BUTTON": {
                "ON_PRESS": "#F8B75C",
                "ON_RELEASE": "#D9A066"
            },
            "START_BUTTON": {
                "ON_PRESS": "#A85A29",
                "ON_RELEASE": "#8F4A1B"
            }
        },
        "TEXT": {
            "LABEL1": "#591603",
            "LABEL2": "#2ECC71",
            "LABEL3": "#F1C40F",
            "LABEL4": "#8E44AD",
        },
    },
    "GAME_VIEW": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "EXIT_BUTTON": {
                "ON_PRESS": "#F8B75C",
                "ON_RELEASE": "#D9A066"
            },
            "WORD_BUTTON": "#E1BA7F",
            "WORD_BUTTON2": "#CE6256",
            "WORD_BUTTON3": "#56B653",
            "WORD_BUTTON4": "#D36C17",
            "TEXTINPUT": {
                "ON_PRESS": "#7B3900",
                "ON_RELEASE": "#7B3900",
            },
            "FEATHERS_FRAME": "#7B3900"
        },
        "TEXT": {
            "TEXTINPUT": "#FFFFFF",
            "LEVEL_TEXT": "#E08D2D",
            "HIDDEN_TIMER_DISPLAYER": "#DC7913"
        },
    },
    "STAT_LEVEL_SELECTION_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "MAIN_BUTTON": {
                "ON_PRESS": "#FFE487",
                "ON_RELEASE": "#F8B75C"
            },
            "EXIT_BUTTON": {
                "ON_PRESS": "#F8B75C",
                "ON_RELEASE": "#D9A066"
            },
        },
        "TEXT": {
            "MAIN_LABEL": "#A4571B"
        }
    },
    "PLAYER_DATA_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "EXIT_BUTTON": {
                "ON_PRESS": "#F8B75C",
                "ON_RELEASE": "#D9A066"
            },
            "DATA_BOX1": "#692F01",
            "DATA_BOX2": "#D58009",
            "DATA_BOX3": "#BE6602",
            "DATA_BOX4": "#FAB953",
            "DATA_BOX5": "#D15F00",
            "DATA_BOX6": "#E5790A",
            "DATA_BOX7": "#FFB444",
            "DATA_BOX8": "#B44100",
        },
        "TEXT": {
            "COLOR1": "#652501",
            "COLOR2": "#FFB444",
        }
    },
    "CUSTOM_KEYBOARD": {
        "BACKGROUND": {
            "MAIN": "#D87F0B",
            "BUTTONS": {
                "ON_PRESS": "#E0B97F",
                "ON_RELEASE": "#E88D1D",
            },
        },
        "TEXT": {
            "DEFAULT": "#FFFFFF"
        },
    },
    "DEFEATE_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "BUTTONS": {
                "ON_PRESS": "#4F1700",
                "ON_RELEASE": "#591602"
            },
            "BOX": {
                "COLOR1": "#591602",
                "COLOR2": "#E19933"
            }
        },
    },
    "VICTORY_SCREEN": {
        "BACKGROUND": {
            "MAIN": "#DC7913",
            "BUTTONS": {
                "ON_PRESS": "#4F1700",
                "ON_RELEASE": "#591602"
            },
            "BOX": {
                "COLOR1": "#591602",
                "COLOR2": "#E19933"
            }
        },
    },
}

player_level = None #This variable will be modified a lot during the game
word_to_find = None #This variable will get the word value if the game is end
copy_of_the_word_to_find = None
definition = None
letter_apparition = []
letter_apparition2 = set()
is_last_game_won = False
is_win_steak = False
is_perfect_win = False
is_clutch_win = False
user_account = None

events_manager = None

user_data_dir = None

def get_word(level: int) -> str:
    if level == "noob":
        word_file_name = "begin_words.json"
    elif level == "medium":
        word_file_name = "medium_words.json"
    elif level == "hard":
        word_file_name = "hard_words.json"
    path_str = resource_find(f"assets/words/{word_file_name}")
    if not path_str:
        raise FileNotFoundError("JSON not in apk")
    json_path = Path(path_str)
    with json_path.open("r", encoding="utf-8") as words_file:
        return random.choice(json.load(words_file))#

def save_user_account():
    path = Path(os.path.join(os.path.join(user_data_dir, "data"), "user_account.json"))
    with path.open("w") as path_file:
        json.dump(user_account, path_file, indent=4)

def troncate(number:float|int, order=2) -> float:
    number = list(str(number))
    i = 0
    for n in number:
        if n == ".":
            i += 1
            break
        i += 1

    troncated_number = float("".join(number[:i+order]))
    return troncated_number

class CreateAccountScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_colors(self) -> str:
        return COLORS_PALETTE

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_colors(self) -> str:
        return COLORS_PALETTE

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

    def check_tutorial_started(self):
        global user_account
        print(f"[check_tutorial_started][user_account={user_account}]")
        if user_account["language"]["french"]["level"][player_level][0]["games_played"] + user_account["language"]["french"]["level"][player_level][1]["games_played"] + user_account["language"]["french"]["level"][player_level][2]["games_played"] == 0:
            self.show_tutorial_or_play_menu()
        else:
            self.manager.transition.direction = "left"
            self.manager.current = "level_selecting_screen"

    def show_tutorial_or_play_menu(self):
        self.menu = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[20, 20, 20, 20],
            size_hint=(0.6, 0.15),
            pos_hint={"center_x":0.5, "center_y":0.5}
        )
        self.menu_indication = Label(
            text="Commencer avec le tutoriel ?",
        )
        self.button_container = BoxLayout(
            orientation="horizontal",
            spacing=10,
            padding=[20, 20, 20, 20]
        )
        self.Yes_button = Button(
            text="OUI",
            bg_color=hex(self.get_colors()["WELCOME_SCREEN"]["BACKGROUND"]["MAIN_BUTTONS"]["ON_PRESS"])
        )
        self.No_button.bind(on_press=self.change_color(button=self.Yes_button, color=self.get_colors()["WELCOME_SCREEN"]["BACKGROUND"]["MAIN_BUTTONS"]["ON_RELEASE"]))
        self.No_button.bind(on_release=self.start_tutorial())#; root.manager.current= "level_selecting_screen"; root.manager.transition.direction="left"
        self.No_button = Button(
            text="Non",
            bg_color=hex(self.get_colors()["WELCOME_SCREEN"]["BACKGROUND"]["MAIN_BUTTONS"]["ON_PRESS"])
        )
        self.No_button.bind(on_press=self.change_color(button=self.No_button, color=self.get_colors()["WELCOME_SCREEN"]["BACKGROUND"]["MAIN_BUTTONS"]["ON_RELEASE"]))
        self.No_button.bind(on_release=self.break_tutorial())
        self.button_container.add_widget(self.No_button)
        self.button_container.add_widget(self.Yes_button)
        self.menu.add_widget(self.menu_indication)
        self.menu.add_widget(self.button_container)
    def start_tutorial(self):
        self.Yes_button.bg_color = hex(self.get_colors()["WELCOME_SCREEN"]["BACKGROUND"]["MAIN_BUTTONS"]["ON_PRESS"])

    def break_tutorial(self):
        self.No_button.bg_color = hex(self.get_colors()["WELCOME_SCREEN"]["BACKGROUND"]["MAIN_BUTTONS"]["ON_PRESS"])
        self.manager.transition.direction = "left"
        self.manager.current = "level_selecting_screen"

    def change_button_color(self, button, color):
        button.bg_color = hex(color)
    
class LevelSelectingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_colors(self) -> str:
        return COLORS_PALETTE
    
    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

    def start_game(self):
        """Check whether any checkbutton is active, and start the game if so."""
        global player_level

        selected = None

        for checkbox in self.ids.values():
            if hasattr(checkbox, "active") and checkbox.active:#hasattr is a python property than permit to verify if an object have an attribut
                selected = checkbox
                break

        if self.ids.check_box1.active:
            player_level = "noob"
        elif self.ids.check_box2.active:
            player_level = "medium"
        elif self.ids.check_box3.active:
            player_level = "hard"

        if selected:
            self.manager.transition.direction = "left"
            self.manager.current = "game_view"
            

class GameView(Screen): 
    displayer = ObjectProperty(None)
    timer_displayer = ObjectProperty(None)
    def __init__(self, **kwargs):
        """
        about attributs:
        self.buttons: list -> her we append the word buttons
        self.word_to_find: None|str -> The word that the player must find.
        self.default_number: int -> The timer value by befault
        self.number: int -> The timer value.
        self.letter_check: set -> stock the letters already validate
        self.stop_time: bool -> Stop the timer if the value the value is False.
        """
        super().__init__(**kwargs)

        self.buttons = []
        self.word_to_find = None
        self.default_number = 40
        self.number = self.default_number
        self.letter_checked = set()
        self.stop_timer = False
        self.default_life = 9
        self.life = self.default_life
        self.default_feather_cleaned_index = 0
        self.default_time_step = 1
        self.feather_cleaned_index = self.default_feather_cleaned_index
        self.time_step = self.default_time_step
        self.running_events = 0
        self.is_block_this_timer = False
        
    def on_pre_enter(self):
        global word_to_find
        global definition
        global copy_of_the_word_to_find

        self.reset_global_variables()
        self.display_player_level()
        self.word_detail = get_word(player_level)
        self.word_to_find = self.word_detail["word"]
        word_to_find = self.word_to_find
        copy_of_the_word_to_find = list(self.word_to_find)
        definition = self.word_detail["definition"]
        self.is_keyboard_closed = True
        self.reset_feathers()
        print(self.word_to_find)
        self.stop_timer = False
        self.is_hidden_timer = False
        self.reset_buttons(target=self.ids.buttons_container)
        self.copy_of_word_to_find = list(copy_of_the_word_to_find)
        Clock.schedule_once(lambda dt:self.buttons_factory(target=self.ids.buttons_container, radius=[10]), 0)
        

    def on_kv_post(self, base_widget):
        self.add_events()

    def add_events(self):
        global events_manager

        if events_manager == None:
            events_manager = EventsManager(keyboard=self.ids.keyboard, displayer=self.ids.event_displayer, timer=self.ids.timer_displayer, main=self, COLORS_PALETTE=COLORS_PALETTE)

    def display_first_letters(self, dt):
        if self.number_of_first_letters_displayed >= self.number_of_first_letters:
            for button in self.buttons:
                if button.id == self.letter_choosed:
                    #reset the color of the last letters printed
                    button.bg_color = get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
            self.get_time()
            self.is_keyboard_closed = False
            return Clock.schedule_once(self.timer, 0)
        self.letter_choosed = random.choice(self.letter_of_word)
        self.letters_choosed.add(self.letter_choosed)
        self.letter_checked.add(self.letter_choosed)
        self.letter_of_word.remove(self.letter_choosed)
        i = 0
        for button in self.buttons:
            if button.id == self.letter_choosed:
                print(f"[display_first_letters][letter={self.letter_choosed}, id={button.id}, First condition]")
                self.buttons[i].text = self.letter_choosed
                button.bg_color = get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
                self.number_of_first_letters_displayed += 1
                self.reduce_word_len()
            elif button.id in self.letters_choosed:
                print(f"[display_first_letters][letter={self.letter_choosed}, id={button.id}, Second condition]")
                if button.bg_color != get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"]):
                    button.bg_color = get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
            i += 1
        print("display_first_letter methode is used")
        Clock.schedule_once(self.display_first_letters, 0.5)


    def reduce_word_len(self):
        self.ids.word_len.text = f"{int(self.ids.word_len.text) - 1}"

    def get_colors(self) -> str:
        return COLORS_PALETTE
    
    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

    def display_player_level(self):
        if player_level == "noob":
            self.ids.level_name.text = "Facile"
            self.ids.level_name.color = self.get_colors()["LEVEL_SELECTING_SCREEN"]["TEXT"]["LABEL2"]
        elif player_level == "medium":
            self.ids.level_name.text = "Corcé"
            self.ids.level_name.color = self.get_colors()["LEVEL_SELECTING_SCREEN"]["TEXT"]["LABEL3"]
        elif player_level == "hard":
            self.ids.level_name.text = "Infernal"
            self.ids.level_name.color = self.get_colors()["LEVEL_SELECTING_SCREEN"]["TEXT"]["LABEL4"]

    def get_level(self) -> str:
        if self.ids.level_name == "Facile":
            return "noob"
        elif self.ids.level_name == "Corcé":
            return "medium"
        else:
            return "hard"
    
    def reset(self, is_reset_displayed_text=False, is_reset_life=False, is_reset_feather_cleaned_index=False, is_reset_letter_checked=False, is_reset_word_len=False):
        """clean the buttons, the word and the keyboard"""
        self.buttons = []
        if is_reset_displayed_text:
            self.displayer.ids.custom_text_input.text = ""
        if is_reset_life:
            self.life = self.default_life
        if is_reset_feather_cleaned_index:
            self.feather_cleaned_index = self.default_feather_cleaned_index
        if is_reset_letter_checked:
            self.letter_checked = set()
        if is_reset_word_len:
            self.ids.word_len.text = "0"
        self.number = self.default_number

    def timer(self, dt):
        if not self.stop_timer:
            if self.number > 1:
                if not self.is_hidden_timer:
                    self.ids.timer_displayer.text = str(self.number - 1)
                else:
                    self.ids.timer_displayer.text = ""
                self.number -= 1
                events_manager.check_event_window(timer=self.number, level=self.get_level())
                if events_manager.locked:
                    if events_manager.current_event != []:
                        events_manager.progress()
                Clock.schedule_once(self.timer, self.time_step)
            else:
                if self.life > 1:
                    if not self.is_hidden_timer:
                        self.ids.timer_displayer.text = str(self.number - 1)
                    else:
                        self.ids.timer_displayer.text = ""
                    self.number -= 1
                    self.remove_feather()
                    events_manager.select_events_time()
                    self.number = self.default_number
                    Clock.schedule_once(self.timer, self.time_step)
                else:
                    self.end_time = time.time()
                    self.time_duration = self.end_time - self.begin_time
                    self.remove_feather()
                    self.reset(is_reset_displayed_text=True, is_reset_life=True, is_reset_feather_cleaned_index=True, is_reset_letter_checked=True, is_reset_word_len=True)
                    self.update_user_data()
                    self.save_user_account()
                    self.go_to_next_screen(transition_duration=1)

    def craft_event_information_box(self):
        self.event_information_box = CustomLabel()
        return self.event_information_box

    def go_to_next_screen(self, transition_duration:int):
        self.manager.transition = WipeTransition(duration=transition_duration)
        self.manager.current = "defeate_screen"
        Clock.schedule_once(lambda dt: self.reset_transition(target=self.manager), 0)

    def remove_feather(self):
        self.ids.feathers_container.children[self.feather_cleaned_index].image_path = self.get_image_path("no_image.png")
        self.feather_cleaned_index += 1
        self.life -= 1

    def reset_feathers(self):
        i = 9
        j = 0
        for feather in self.ids.feathers_container.children:
            self.ids.feathers_container.children[j].image_path = self.get_image_path(f"f{i}.png")
            i -= 1
            j += 1
        
    def reset_transition(self, target):
        target.transition = SlideTransition()
        
    def buttons_factory(self, target, radius=15, button_bg_color=get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"]), bold=True):
        """Creat button dynamically
        * number : The number of buttons
        * target : The layout where the buttons will be set
        * radius : The buttons corners radius
        * button_bg_color : the button background color
        * bold: True if the text is bold, else False
        """

        if self.copy_of_word_to_find != []:
            for letter in self.copy_of_word_to_find:
                button = CustomButton(id=f"{letter}", text="?", bold=bold)
                button.bind(size=lambda instance, size:setattr(instance, "font_size", min(instance.width, instance.height) * 0.75 ))
                button.radius = radius
                button.bg_color = button_bg_color
                self.save_button(button)
                target.add_widget(button)
                self.copy_of_word_to_find = self.copy_of_word_to_find[1:]
                self.ids.word_len.text = f"{int(self.ids.word_len.text) + 1}"
                if self.copy_of_word_to_find == []:
                    self.letter_of_word = list(set(word_to_find))
                    self.number_of_first_letters = int(len(word_to_find) * 0.3)
                    print(f"self.number_of_first_letters == {self.number_of_first_letters}")
                    if self.number_of_first_letters < 1:
                        self.number_of_first_letters = 1
                    self.number_of_first_letters_displayed = 0
                    self.letters_choosed = set()
                    Clock.schedule_once(self.display_first_letters, 0)
                    break
                Clock.schedule_once(lambda dt:self.buttons_factory(target=self.ids.buttons_container, radius=[10]), 0.4)
                break

    def reset_buttons(self, target):
        target.clear_widgets()
        self.buttons = []

    def save_button(self, button):
        self.buttons.append(button)

    def get_time(self):
        self.begin_time = time.time()

    def update_user_data(self):
        """I add the 0 index at the player_level list because the json module modify it in a list type that contain the list"""
        global user_account

        user_account["language"]["french"]["level"][player_level][0]["games_played"] += 1
        user_account["language"]["french"]["level"][player_level][0]["total_defeates"] += 1
        user_account["language"]["french"]["level"][player_level][0]["win_streak"] = 0
        user_account["language"]["french"]["level"][player_level][0]["perfect_wins"] = 0
        user_account["language"]["french"]["level"][player_level][0]["defeate_rate"] = troncate((user_account["language"]["french"]["level"][player_level][0]["total_defeates"] / user_account["language"]["french"]["level"][player_level][0]["games_played"]), order=2) * 100
        user_account["language"]["french"]["level"][player_level][0]["win_rate"] = 100 - user_account["language"]["french"]["level"][player_level][0]["defeate_rate"]
        user_account["language"]["french"]["level"][player_level][0]["last_game_duration"] = {
            "expression": f"{time.localtime(self.time_duration).tm_min}:{time.localtime(self.time_duration).tm_sec}",
            "seconds": self.time_duration
        }
        if user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["seconds"] < user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"]:
            user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"] = user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["expression"]
            user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"] = user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["seconds"]

        user_account["language"]["french"]["level"][player_level][0]["last_game_time"]["date"] = f"{time.localtime(self.end_time).tm_mday}/{time.localtime(self.end_time).tm_mon}/{time.localtime(self.end_time).tm_year}"
        user_account["language"]["french"]["level"][player_level][0]["last_game_time"]["hour"] = f"{time.localtime(self.end_time).tm_hour}:{time.localtime(self.end_time).tm_min}:{time.localtime(self.end_time).tm_sec}"

    def save_user_account(self):
        path = Path(os.path.join(os.path.join(user_data_dir, "data"), "user_account.json"))
        with path.open("w") as path_file:
            json.dump(user_account, path_file, indent=4)

    def reset_global_variables(self):
        global word_to_find
        global letter_apparition
        global letter_apparition2

        word_to_find = None
        letter_apparition = []
        letter_apparition2 = set()

class DefeateScreen(Screen):
    def __init__(self, **kwargs):
        """
        about attributs
        self.buttons: list -> stock the words buttons
        self.button_index: int -> Used in the buttons_animation classe methode for point out the animated button index.
        """
        super().__init__(**kwargs)
        self.buttons = []
        self.button_index = 0

    def get_colors(self) -> str:
        return COLORS_PALETTE
    
    def on_pre_enter(self):
        global letter_apparition2

        self.ids.defintion_viewer.ids.custom_text_input.text = ""
        self.buttons_factory(target=self.ids.buttons_container2)
        Clock.schedule_once(self.buttons_animation, 1.5)

    def buttons_factory(self, target):
        self.clean_buttons(target=target)
        for i in range(len(word_to_find)):
            button = CustomButton(text="", bold=True)
            button.bind(size=lambda instance, size:setattr(instance, "font_size", min(instance.width,instance.  height)* 0.75 ))
            button.radius = [15]
            button.bg_color = get_color_from_hex(self.get_colors()["DEFEATE_SCREEN"]["BACKGROUND"]["MAIN"])
            self.buttons.append(button)
        for button in self.buttons:
            target.add_widget(button)

    def clean_buttons(self, target):
        self.buttons = []
        for child in target.children[:]:
            if isinstance(child, CustomButton):
                target.remove_widget(child)
                print("True")
            else:
                print("False")

    def buttons_animation(self, dt, button_bg_color=get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])):
        """This function is used for animate the buttons apparition """

        self.buttons[self.button_index].bg_color = button_bg_color
        self.button_index += 1
        if (self.button_index + 1) <= len(word_to_find):
            Clock.schedule_once(self.buttons_animation, 0.1)
        else:
            self.button_index = 0 # reseting of the button_index
            Clock.schedule_once(self.print_letters_in_letter_apparition, 0.5)

    def print_letters_in_letter_apparition(self, dt):
        """Print the letters on the buttons"""
        global letter_apparition
        global letter_apparition2

        print(letter_apparition)
        i = 0
        for letter in word_to_find:
            if letter_apparition == []:
                break
            if letter_apparition[0] == letter:
                self.buttons[i].text = letter.upper()
            i += 1
        if letter_apparition != []:
            letter_apparition2.add(letter_apparition[0])
        letter_apparition = letter_apparition[1:]
        if letter_apparition != []:
            Clock.schedule_once(self.print_letters_in_letter_apparition, 0.5)
        else:
            Clock.schedule_once(self.print_last_letters, 0.8)

    def print_last_letters(self, dt):
        global letter_apparition2

        for letter in list(word_to_find):
            if not letter in letter_apparition2:
                i = 0
                for letter2 in list(word_to_find):
                    if letter2 == letter:
                        self.buttons[i].text = letter.upper()
                    i += 1
                del(i)
                letter_apparition2.add(letter)
                Clock.schedule_once(self.print_last_letters, 1)
                break

        if  self.is_all_letters_printed():
            self.is_break = False
            Clock.schedule_once(self.print_definition, 0.01)

    def print_definition(self, dt):
        global definition
    
        for letter in definition:
            if self.is_break:
                self.is_break = False
                break
            else:
                self.ids.defintion_viewer.ids.custom_text_input.text += letter
                definition = "".join(list(definition)[1:])
                if definition == "":
                    self.is_break = True
                Clock.schedule_once(self.print_definition, 0.01)
                break

    def is_all_letters_printed(self):
        word = ""
        for button in self.buttons:
            if button.text == "":
                break
            word += button.text
        if word == word_to_find.upper():
            return True
        
    def print_definitin_on_thread(self):
        for letter in definition:
            Clock.schedule_once(lambda dt:self.update_viewer(letter), 0.01)
        
    def update_viewer(self, dt, letter):
        self.ids.defintion_textinput.text += letter
                  
class VictoryScreen(Screen):
    def __init__(self, **kwargs):
        """
        about attributs
        self.buttons: list -> stock the words buttons
        self.button_index: int -> Used in the buttons_animation classe methode for point out the animated button index.
        """
        super().__init__(**kwargs)
        self.buttons = []
        self.button_index = 0
        self.is_break = False

    def get_colors(self) -> str:
        return COLORS_PALETTE

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

    def on_pre_enter(self):
        global letter_apparition2

        if self.is_break:
            self.is_break = False
        self.ids.defintion_viewer.ids.custom_text_input.text = ""
        self.buttons_factory(target=self.ids.buttons_container2)
        Clock.schedule_once(self.buttons_animation, 1.5)

    def buttons_factory(self, target):
        self.clean_buttons(target=target)
        for i in range(len(word_to_find)):
            button = CustomButton(text="", bold=True)
            button.bind(size=lambda instance, size:setattr(instance, "font_size", min(instance.width,instance.  height)* 0.75 ))
            button.radius = [15]
            button.bg_color = get_color_from_hex(self.get_colors()["DEFEATE_SCREEN"]["BACKGROUND"]["MAIN"])
            self.buttons.append(button)
        for button in self.buttons:
            target.add_widget(button)

    def clean_buttons(self, target):
        self.buttons = []
        for child in target.children[:]:
            if isinstance(child, CustomButton):
                target.remove_widget(child)

    def buttons_animation(self, dt, button_bg_color=get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"])):
        """This function is used for animate the buttons apparition """

        if not self.is_break:
            self.buttons[self.button_index].bg_color = button_bg_color
            self.button_index += 1
            if (self.button_index + 1) <= len(word_to_find):
                Clock.schedule_once(self.buttons_animation, 0.1)
            else:
                self.button_index = 0 # reseting of the button_index
                Clock.schedule_once(self.print_all_letters, 0.3)

    def print_all_letters(self, dt):
        """Print the letters on the buttons"""
        if not self.is_break:
            if self.button_index < len(word_to_find) - 1:
                self.buttons[self.button_index].text = word_to_find[self.button_index]
                self.button_index += 1
                Clock.schedule_once(self.print_all_letters, 0.3)
            elif self.button_index == len(word_to_find) - 1:
                self.buttons[self.button_index].text = word_to_find[-1]
                self.button_index = 0 #Reseting of self.button_index
                self.is_break = False
                Clock.schedule_once(self.print_definition, 0.01)

    def print_definition(self, dt):
        global definition

        if not self.is_break:
            for letter in definition:
                if self.is_break:
                    self.is_break = False
                    break
                else:
                    self.ids.defintion_viewer.ids.custom_text_input.text += letter
                    definition = "".join(list(definition)[1:])
                    if definition == "":
                        self.is_break = True
                    Clock.schedule_once(self.print_definition, 0.01)
                    break

    def pass_menu(self):
        if not self.is_break:
            self.is_break = True

class StatLevelSelectingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_colors(self):
        return COLORS_PALETTE

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)
    
    def update_player_level(self, level:"str"):
        global player_level

        player_level = level    

class PlayerDataScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_colors(self):
        return COLORS_PALETTE

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

    def on_pre_enter(self):
        if player_level == "noob":
            self.ids.level_label.text = "FACILE"
        elif player_level == "medium":
            self.ids.level_label.text = "CORCE"
        elif player_level == "hard":
            self.ids.level_label.text = "INFERNAL"
        self.update_simples_data()
        self.update_specials_data()
        

    def update_simples_data(self):
        self.ids.user_points.text = str(user_account["language"]["french"]["level"][player_level][0]["points"])
        self.ids.games_played.text = str(user_account["language"]["french"]["level"][player_level][0]["games_played"])
        self.ids.victories.text = str(user_account["language"]["french"]["level"][player_level][0]["total_wins"])
        self.ids.defeates.text = str(user_account["language"]["french"]["level"][player_level][0]["total_defeates"])
        self.ids.date.text = f"le {(user_account['language']['french']['level'][player_level][0]['last_game_time']['date'])}"
        self.ids.hour.text = f"le {(user_account['language']['french']['level'][player_level][0]['last_game_time']['hour'])}"

    def update_specials_data(self):
        self.ids.used_points.text = f"le {(user_account['language']['french']['level'][player_level][0]['used_points'])}"

    def update_achievements(self):
        self.ids.achievement1.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot1"]["achievement1"]
        self.ids.achievement2.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot1"]["achievement2"]
        self.ids.achievement3.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot1"]["achievement3"]
        self.ids.achievement4.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot2"]["achievement1"]
        self.ids.achievement5.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot2"]["achievement2"]
        self.ids.achievement6.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot2"]["achievement3"]
        self.ids.achievement7.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot3"]["achievement1"]
        self.ids.achievement8.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot3"]["achievement2"]
        self.ids.achievement9.path = user_account["language"]["french"]["level"][player_level][0]["achievements"][0]["lot3"]["achievement3"]

class KeyBordCraftingLab(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_break = False
        self.default_sentence = "Salut je me nomme Pendu ! Veux-tu jouer avec moi ?\nSi oui je te montre les règle du jeu qui sont archi simples.\nDabord l'algorithme choisi un mot aleatoire parmis de nombreux mots que tu devra trouver au fur et a mesure du jeu. tu disposera d'un nombre limité de tentative en fonction de ton niveau de jeu, simple non ? \n Alors on commence ?"

    def on_pre_enter(self):
        self.sentence = self.default_sentence
        Clock.schedule_once(self.write_sentence, 0.01)

    def get_colors(self) -> str:
        return COLORS_PALETTE

    def write_sentence(self, dt):
        for letter in self.sentence:
            if self.is_break:
                self.ids.note.ids.custom_text_input.text = ""
                self.sentence = self.default_sentence
                self.is_break = False
                Clock.schedule_once(self.write_sentence, 0.08)
            if self.sentence == "":
                self.is_break = True
                break
            self.ids.note.ids.custom_text_input.text += letter
            self.sentence = "".join(list(self.sentence)[1:])
            Clock.schedule_once(self.write_sentence, 0.01)
            break

    def reset_sentence(self):
        if self.is_break == True:
            self.is_break = False
            self.sentence = self.default_sentence
            Clock.schedule_once(self.write_sentence, 0.01)
        if self.is_break == False:
            self.is_break = True

class Manager(ScreenManager):
    welcome_screen = ObjectProperty(None)

class CustomButton(Button):
    bg_color = ListProperty([0, 0, 0, 0])
    radius = ListProperty([20])
    keyboard = ObjectProperty(None)
    id = StringProperty(None)

class CustomLabel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        self.size_hint = (0.65, 1)
        self.pos_hint = {"x":0.3, "center_y":0.5}
        self.padding = [20, 20, 20, 20]
        with self.canvas.before:
            Color(rgb=get_color_from_hex(self.get_colors()["DEFEATE_SCREEN"]["BACKGROUND"]["BOX"]["COLOR2"]))
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[15]
            )
        self.scroll = ScrollView(do_scroll_x=False)
        self.event_information_label = Label(
            text="",
            color=get_color_from_hex("#FFFFFF")
        )
        self.event_information_label.size_hint_y = None
        self.event_information_label.bind(
            width=lambda instance, value: setattr(instance, "text_size", (value, None))
        )
        self.event_information_label.bind(
            texture_size=lambda instance, value: setattr(instance, "height", value[1])
        )
        self.scroll.add_widget(self.event_information_label)
        self.add_widget(self.scroll)
        
        self.bind(pos=self._update_rect, size=self._update_rect)

    def get_colors(self) -> str:
        return COLORS_PALETTE
        
    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class FeatherFrame(BoxLayout):
    bg_color = ListProperty([0, 0, 0, 0])
    image_path = StringProperty(None)

    def get_colors(self) -> str:
        return COLORS_PALETTE

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

class CustomTextInput(BoxLayout):
    bg_color = ListProperty([0, 0, 0, 0])
    radius = ListProperty([20])
    text_color = [1, 1, 1, 1]
    default_value = NumericProperty(0.70)
    multiline = BooleanProperty(False)
    halign = StringProperty(None)#"center")
    valign = StringProperty(None)#"center")

class CustomKeyBoard(FloatLayout):
    bg_color = StringProperty(COLORS_PALETTE["CUSTOM_KEYBOARD"]["BACKGROUND"]["MAIN"])
    radius = ListProperty([15])
    button_comon_color = ListProperty(None)
    general_target = ObjectProperty(None)
    target_input = ObjectProperty(None)
    on_grown_up = False

    def get_colors(self):
        return COLORS_PALETTE

    def get_word_methode(self, level: int) -> str:
        return get_word(level)

    def get_image_path(self, image: str) -> str:
        return os.path.join(".", "assets", "images", "png", image)

    def on_key_press(self, letter:str):
        """Add an word to the target. the target must be a textinput"""
        if self.general_target.is_keyboard_closed:
            return
        if self.target_input:
            if not self.on_grown_up:
                self.target_input.ids.custom_text_input.text = letter
            else:
                self.target_input.ids.custom_text_input.text = letter.upper()

    def reset_transition(self, target):
        target.transition = SlideTransition()

    def validate_letter(self):
        """Check if the letter is or not in the text or if the letter have been already validate"""
        global word_to_find
        global letter_apparition

        if self.general_target.is_keyboard_closed:
            return
        if self.target_input: #Check if the target is not None type
            letter = self.target_input.ids.custom_text_input.text.lower()
            if letter != "":
                self.is_letter_in_word = False
                self.is_end_game = False
                self.is_victory = False
                self.print_letter_or_pass(letter=letter)
                self.target_input.ids.custom_text_input.text = ""
                if not letter in self.general_target.letter_checked:
                    if not self.is_letter_in_word:
                        self.remove_feather()
                    else: #The letter is in the word
                        letter_apparition.append(letter)
                        if self.is_victory:
                            self.is_end_game = True
                    if self.is_end_game:
                        self.end_time = time.time()
                        self.time_duration = self.end_time - self.general_target.begin_time
                        self.reset_game()
                    else: # The game continue
                        self.general_target.number = self.general_target.default_number
                        self.general_target.timer_displayer.text = str(self.general_target.number)
                        events_manager.select_events_time()
                        
                    self.general_target.letter_checked.add(letter)

    def print_letter_or_pass(self, letter):
        """This function print the letter in the custombuttons if it's in word to find"""
        i = 0
        for button in self.general_target.buttons:
            print(f"[print_letter_or_pass][button.id={button.id}]")
            if button.id == letter:
                self.general_target.buttons[i].text = letter
                self.general_target.buttons[i].bg_color = get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON4"])
                self.is_letter_in_word = True
                self.reduce_word_len()
            i += 1
        if self.is_letter_in_word:
            self.check_victory(letter)
        i = 0
        while i == 0:
            Clock.schedule_once(lambda dt:self.change_button_color(letter=letter), 0.5)
            break

    def change_button_color(self, letter):
        i = 0
        for button in self.general_target.buttons:
            if button.id == letter:
                if button.bg_color != get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON"]):
                    self.general_target.buttons[i].bg_color = get_color_from_hex(COLORS_PALETTE["GAME_VIEW"]["BACKGROUND"]["WORD_BUTTON3"])
            i += 1

    def check_victory(self, letter:str) -> bool:
        global copy_of_the_word_to_find
        i = 0
        for button in self.general_target.buttons:
            if button.text != "?":
                i += 1
        if i == len(self.general_target.word_to_find):
            self.is_victory = True

    def reduce_word_len(self):
        self.general_target.ids.word_len.text = f"{int(self.general_target.ids.word_len.text) - 1}"
    
    def remove_feather(self):
        """This function del a feather"""
        if self.general_target.life > 1:
            self.general_target.ids.feathers_container.children[self.general_target.feather_cleaned_index].image_path = self.get_image_path("no_image.png")
            self.general_target.feather_cleaned_index += 1
            self.general_target.life -= 1
        else:
            self.general_target.ids.feathers_container.children[self.general_target.feather_cleaned_index].image_path = self.get_image_path("no_image.png")
            self.general_target.feather_cleaned_index += 1
            self.general_target.life -= 1
            self.is_end_game = True

    def go_to_next_screen(self, transition_duration:int):
        self.general_target.manager.transition = WipeTransition(duration=transition_duration)
        if self.is_victory:
            self.general_target.manager.current = "victory_screen"
        else:
            self.general_target.manager.current = "defeate_screen"
        Clock.schedule_once(lambda dt: self.reset_transition(target=self.general_target.manager), 0)

    def checking_game_statut(self):
        """Check if all feathers are delected for finish the game"""
        print("checking_game_statut function has been activate")
        i = 0
        for feather_frame in self.general_target.ids.feathers_container.children:
            if feather_frame.image_path != "":
                break
            i += 1
        if len(self.general_target.ids.feathers_container.children) == i:
            self.is_end_game = True

    def reset_game(self):
        global word_to_find
        global is_last_game_won
        global is_win_steak
        global is_perfect_win
        global is_clutch_win
        global copy_of_the_word_to_find

        if not self.is_victory:
            if is_last_game_won:
                is_last_game_won = False
                is_win_steak = False
            self.update_user_data(is_win=False)
        else:
            if self.general_target.life == self.general_target.default_life:
                is_perfect_win = True
            elif self.general_target.life == 1:
                is_clutch_win = True
                is_perfect_win = False
            else:
                is_perfect_win = False
                is_clutch_win = False
            self.update_user_data(is_win=True)
        self.save_user_account()
        copy_of_the_word_to_find = None
        self.general_target.life = self.general_target.default_life
        self.general_target.feather_cleaned_index = self.general_target.default_feather_cleaned_index
        self.general_target.letter_checked = set()
        self.general_target.stop_timer = True
        self.general_target.number = self.general_target.default_number
        self.general_target.timer_displayer.text = str(self.general_target.number)
        word_to_find = self.general_target.word_to_find
        self.general_target.word_to_find = None
        self.general_target.ids.displayer.ids.custom_text_input.text = ""
        self.general_target.ids.word_len.text = "0"
        self.go_to_next_screen(transition_duration=1)
        

    def update_global_variables_on_win(self):
        global is_last_game_won
        global is_win_steak
        global is_perfect_win
    
        if is_last_game_won:
            is_win_steak = True
        elif not is_last_game_won:
            is_last_game_won = True
        if self.general_target.life == self.general_target.default_life:
            is_perfect_win = True

    def update_user_data(self, is_win=False):
        global user_account

        if is_win:
            user_account["language"]["french"]["level"][player_level][0]["games_played"] += 1
            user_account["language"]["french"]["level"][player_level][0]["earned_points"] += self.general_target.life
            user_account["language"]["french"]["level"][player_level][0]["points"] += 1
            user_account["language"]["french"]["level"][player_level][0]["total_wins"] += 1
            if is_win_steak:
                user_account["language"]["french"]["level"][player_level][0]["win_streak"] += 1
                if user_account["language"]["french"]["level"][player_level][0]["win_streak"] > user_account["language"]["french"]["level"][player_level][0]["best_win_steak"]:
                    user_account["language"]["french"]["level"][player_level][0]["best_win_steak"] = user_account["language"]["french"]["level"][player_level][0]["win_streak"]
            else:
                if user_account["language"]["french"]["level"][player_level][0]["win_streak"] > user_account["language"]["french"]["level"][player_level][0]["best_win_steak"]:
                    user_account["language"]["french"]["level"][player_level][0]["best_win_steak"] = user_account["language"]["french"]["level"][player_level][0]["win_streak"]
                user_account["language"]["french"]["level"][player_level][0]["win_streak"] = 0
            if is_perfect_win:
                user_account["language"]["french"]["level"][player_level][0]["perfect_wins"] += 1
                if user_account["language"]["french"]["level"][player_level][0]["perfect_wins"] > user_account["language"]["french"]["level"][player_level][0]["best_perfect_win"]:
                    user_account["language"]["french"]["level"][player_level][0]["best_perfect_win"] = user_account["language"]["french"]["level"][player_level][0]["perfect_wins"]
            else:
                if user_account["language"]["french"]["level"][player_level][0]["perfect_wins"] > user_account["language"]["french"]["level"][player_level][0]["best_perfect_win"]:
                    user_account["language"]["french"]["level"][player_level][0]["best_perfect_win"] = user_account["language"]["french"]["level"][player_level][0]["perfect_wins"]
                user_account["language"]["french"]["level"][player_level][0]["perfect_wins"] = 0
            if is_clutch_win:
                user_account["language"]["french"]["level"][player_level][0]["clutch_wins"] += 1
            user_account["language"]["french"]["level"][player_level][0]["win_rate"] = troncate(user_account["language"]["french"]["level"][player_level][0]["total_wins"] / user_account["language"]["french"]["level"][player_level][0]["games_played"], order=2) * 100
            user_account["language"]["french"]["level"][player_level][0]["defeate_rate"] = 100 - user_account["language"]["french"]["level"][player_level][0]["win_rate"]
            user_account["language"]["french"]["level"][player_level][0]["last_game_duration"] = {
                "expression": f"{time.localtime(self.time_duration).tm_min}:{time.localtime(self.time_duration).tm_sec}",
                "seconds": self.time_duration
            }
            if user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["seconds"] < user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"]:
                user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"] = user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["expression"]
                user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"] = user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["seconds"]
    
            user_account["language"]["french"]["level"][player_level][0]["last_game_time"]["date"] = f"{time.localtime(self.end_time).tm_mday}/{time.localtime(self.end_time).tm_mon}/{time.localtime(self.end_time).tm_year}"
            user_account["language"]["french"]["level"][player_level][0]["last_game_time"]["hour"] = f"{time.localtime(self.end_time).tm_hour}:{time.localtime(self.end_time).tm_min}:{time.localtime(self.end_time).tm_sec}"
        if not is_win:
            user_account["language"]["french"]["level"][player_level][0]["games_played"] += 1
            user_account["language"]["french"]["level"][player_level][0]["total_defeates"] += 1
            user_account["language"]["french"]["level"][player_level][0]["win_streak"] = 0
            user_account["language"]["french"]["level"][player_level][0]["defeate_rate"] = troncate((user_account["language"]["french"]["level"][player_level][0]["total_defeates"] / user_account["language"]["french"]["level"][player_level][0]["games_played"]), order=2) * 100
            user_account["language"]["french"]["level"][player_level][0]["win_rate"] = 100 - user_account["language"]["french"]["level"][player_level][0]["defeate_rate"]
            user_account["language"]["french"]["level"][player_level][0]["last_game_duration"] = {
                "expression": f"{time.localtime(self.time_duration).tm_min}:{time.localtime(self.time_duration).tm_sec}",
                "seconds": self.time_duration
            }
            if user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["seconds"] < user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"]:
                user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["expression"] = user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["expression"]
                user_account["language"]["french"]["level"][player_level][0]["best_game_duration"]["seconds"] = user_account["language"]["french"]["level"][player_level][0]["last_game_duration"]["seconds"]
    
            user_account["language"]["french"]["level"][player_level][0]["last_game_time"]["date"] = f"{time.localtime(self.end_time).tm_mday}/{time.localtime(self.end_time).tm_mon}/{time.localtime(self.end_time).tm_year}"
            user_account["language"]["french"]["level"][player_level][0]["last_game_time"]["hour"] = f"{time.localtime(self.end_time).tm_hour}:{time.localtime(self.end_time).tm_min}:{time.localtime(self.end_time).tm_sec}"

    def save_user_account(self):
        path = Path(os.path.join(os.path.join(user_data_dir, "data"), "user_account.json"))
        with path.open("w") as path_file:
            json.dump(user_account, path_file, indent=4)
    
    def grown_or_down(self):
        if self.a0_button.text.islower():
            self.a0_button.text = self.a0_button.text.upper()
            self.a1_button.text = (self.a1_button.text).upper()
            self.a2_button.text = (self.a2_button.text).upper()
            self.e0_button.text = (self.e0_button.text).upper()
            self.e1_button.text = (self.e1_button.text).upper()
            self.e2_button.text = (self.e2_button.text).upper()
            self.u0_button.text = (self.u0_button.text).upper()
            self.i0_button.text = (self.i0_button.text).upper()
            self.i1_button.text = (self.i1_button.text).upper()
            self.o0_button.text = (self.o0_button.text).upper()
            self.a3_button.text = (self.a3_button.text).upper()
            self.z_button.text = str( self.z_button.text).upper()
            self.e3_button.text = (self.e3_button.text).upper()
            self.r_button.text = (self.r_button.text).upper()
            self.t_button.text = (self.t_button.text).upper()
            self.y_button.text = (self.y_button.text).upper()
            self.u_button.text = (self.u_button.text).upper()
            self.i2_button.text = (self.i2_button.text).upper()
            self.o1_button.text = (self.o1_button.text).upper()
            self.p_button.text = (self.p_button.text).upper()
            self.q_button.text = (self.q_button.text).upper()
            self.s_button.text = (self.s_button.text).upper()
            self.d_button.text = (self.d_button.text).upper()
            self.f_button.text = (self.f_button.text).upper()
            self.g_button.text = (self.g_button.text).upper()
            self.h_button.text = (self.h_button.text).upper()
            self.j_button.text = (self.j_button.text).upper()
            self.k_button.text = (self.k_button.text).upper()
            self.l_button.text = (self.l_button.text).upper()
            self.m_button.text = (self.m_button.text).upper()
            self.w_button.text = (self.w_button.text).upper()
            self.x_button.text = (self.x_button.text).upper()
            self.c_button.text = (self.c_button.text).upper()
            self.v_button.text = (self.v_button.text).upper()
            self.b_button.text = (self.b_button.text).upper()
            self.n_button.text = (self.n_button.text).upper()
            self.on_grown_up = True
        else:
            self.a0_button.text = (self.a0_button.text).lower()
            self.a1_button.text = (self.a1_button.text).lower()
            self.a2_button.text = (self.a2_button.text).lower()
            self.e0_button.text = (self.e0_button.text).lower()
            self.e1_button.text = (self.e1_button.text).lower()
            self.e2_button.text = (self.e2_button.text).lower()
            self.u0_button.text = (self.u0_button.text).lower()
            self.i0_button.text = (self.i0_button.text).lower()
            self.i1_button.text = (self.i1_button.text).lower()
            self.o0_button.text = (self.o0_button.text).lower()
            self.a3_button.text = (self.a3_button.text).lower()
            self.z_button.text= (self.z_button.text).lower()
            self.e3_button.text = (self.e3_button.text).lower()
            self.r_button.text= (self.r_button.text).lower()
            self.t_button.text= (self.t_button.text).lower()
            self.y_button.text= (self.y_button.text).lower()
            self.u_button.text= (self.u_button.text).lower()
            self.i2_button.text = (self.i2_button.text).lower()
            self.o1_button.text = (self.o1_button.text).lower()
            self.p_button.text= (self.p_button.text).lower()
            self.q_button.text= (self.q_button.text).lower()
            self.s_button.text= (self.s_button.text).lower()
            self.d_button.text= (self.d_button.text).lower()
            self.f_button.text = (self.f_button.text).lower()
            self.g_button.text= (self.g_button.text).lower()
            self.h_button.text= (self.h_button.text).lower()
            self.j_button.text= (self.j_button.text).lower()
            self.k_button.text= (self.k_button.text).lower()
            self.l_button.text= (self.l_button.text).lower()
            self.m_button.text= (self.m_button.text).lower()
            self.w_button.text= (self.w_button.text).lower()
            self.x_button.text= (self.x_button.text).lower()
            self.c_button.text= (self.c_button.text).lower()
            self.v_button.text= (self.v_button.text).lower()
            self.b_button.text= (self.b_button.text).lower()
            self.n_button.text= (self.n_button.text).lower()
            self.on_grown_up = False
    
class MainApp(App):
    def build(self):
        global user_data_dir

        user_data_dir = App.get_running_app().user_data_dir
        return Manager()

    def on_start(self):
        global user_account

        self.step1 = False
        self.step2 = False
        self.data_dir = os.path.join(user_data_dir, "data")

        self.check_step1()
        if self.step1 == True:
            self.check_step2()
            if self.step2 == True:
                self.get_user_account()
                self.go_to_next_screen(transition_duration=0, screen_name="welcome_screen")
            else:
                self.create_user_account()
                user_account = self.default_user_account
                self.go_to_next_screen(transition_duration=0, screen_name="welcome_screen")
        else:
            self.create_folder()
            self.create_user_account()
            user_account = self.default_user_account
            self.go_to_next_screen(transition_duration=0, screen_name="welcome_screen")

    def check_step1(self):
        if os.path.exists(os.path.join(user_data_dir, "data")):
            self.step1 = True

    def check_step2(self):
        if os.path.exists(os.path.join(self.data_dir, "user_account.json")):
            self.step2 = True

    def create_folder(self):
        os.mkdir(self.data_dir)#os.path.join(user_data_dir, "file"))

    def create_user_account(self):
        self.default_user_stat = {
            "games_played": 0,
            "earned_points": 0,
            "points": 0,
            "lost_points": 0,
            "total_wins": 0,
            "total_defeates": 0,
            "win_streak": 0,
            "best_win_steak": 0,
            "loss_streak": 0,
            "perfect_wins": 0,
            "used_points": 0,
            "best_perfect_win": 0,
            "loss_wins": 0,
            "best_loss_wins": 0,
            "clutch_wins": 0,
            "help_buttons_used": 0,
            "win_rate": 0.0,
            "defeate_rate": 0.0,
            "achievements": {
                "lot1": {
                    "achievement1": "",
                    "achievement2": "",
                    "achievement3": "",
                },
                "lot2": {
                    "achievement1": "",
                    "achievement2": "",
                    "achievement3": "",
                },
                "lot3": {
                    "achievement1": "",
                    "achievement2": "",
                    "achievement3": "",
                },
            },
            "last_game_duration": {
                "expression": "00/00/0000",
                "seconds": 0
            },
            "best_game_duration": {
                "expression": "00/00/0000",
                "seconds": 0
            },
            "last_game_time": {
                "date": "00/00/0000",
                "hour": "00/00/0000"
            },
            "game_duration": None,
        },
        self.default_user_account = {
            "language": {
                "french": {
                    "level": {
                        "noob": self.default_user_stat,
                        "medium": self.default_user_stat,
                        "hard": self.default_user_stat
                    }
                }
            }
        }
        path = Path(os.path.join(self.data_dir, "user_account.json"))
        with path.open("w") as path_file:
            json.dump(self.default_user_account, path_file, indent=4)

    def get_user_account(self):
        global user_account

        path = Path(os.path.join(self.data_dir, "user_account.json"))
        with path.open("r") as path_file:
            user_account = json.load(path_file)

    def go_to_next_screen(self, transition_duration:int, screen_name:str):
        self.root.transition=WipeTransition(duration=transition_duration)
        self.root.current=screen_name
        self.reset_transition(target=self.root)

    def reset_transition(self, target):
        target.transition = SlideTransition()

if __name__ == "__main__":
    mainapp = MainApp()
    mainapp.run()
