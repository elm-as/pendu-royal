"""Pendu Royal — point d'entrée.

Organisation :
    pendu/config.py        constantes (palette, niveaux, modes, indices)
    pendu/words.py         dictionnaire
    pendu/game.py          règles (Round, Session), sans Kivy
    pendu/events.py        événements aléatoires, sans Kivy
    pendu/storage.py       profil joueur (sauvegarde atomique, migration)
    pendu/achievements.py  succès
    pendu/ui/              écrans et composants Kivy (+ pendu.kv)
"""
import os
from datetime import date

from kivy.utils import platform

if platform not in ("android", "ios"):
    from kivy.config import Config
    Config.set("graphics", "width", "420")
    Config.set("graphics", "height", "860")
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import FadeTransition, ScreenManager, SlideTransition

from pendu.audio import Audio
from pendu.config import COLORS, ROOT, font
from pendu.storage import Profile
from pendu.ui import widgets
from pendu.ui.game_screen import GameScreen
from pendu.ui.screens import (
    AchievementsScreen, HomeScreen, ModesScreen, ResultScreen, SettingsScreen, StatsScreen,
    TutorialScreen,
)
from pendu.words import WordBank, fold

LabelBase.register("Body", fn_regular=font("AlegreyaSans-Medium"), fn_bold=font("AlegreyaSans-ExtraBold"))
LabelBase.register("Title", fn_regular=font("CinzelDecorative-Bold"))
for name in ("RoundButton", "Panel", "WordBoard", "Keyboard", "KeyButton", "FeatherBar", "Feather",
             "Gallows", "TimerRing", "Toast", "LetterTile"):
    Factory.register(name, cls=getattr(widgets, name))


class PenduRoyalApp(App):
    title = "Pendu Royal"
    icon = str(ROOT / "assets" / "images" / "png" / "icon.png")

    def build(self):
        Window.clearcolor = widgets.rgba("bg_bottom")
        self.profile = Profile(os.path.join(self.user_data_dir, "data"))
        self.bank = WordBank()
        self.audio = Audio(self.profile.settings)
        self.bg_texture = widgets.vertical_gradient(COLORS["bg_top"], COLORS["bg_bottom"])
        self.greeted = False           # le roi salue Manassé une fois par lancement
        self.fake_crash_done = False   # un seul faux plantage par lancement
        Builder.load_file(str(ROOT / "pendu" / "ui" / "pendu.kv"))

        sm = ScreenManager(transition=SlideTransition(duration=0.25))
        for cls, name in ((HomeScreen, "home"), (ModesScreen, "modes"), (GameScreen, "game"),
                          (ResultScreen, "result"), (StatsScreen, "stats"),
                          (AchievementsScreen, "achievements"), (SettingsScreen, "settings"),
                          (TutorialScreen, "tutorial")):
            sm.add_widget(cls(name=name))
        Window.bind(on_keyboard=self._on_keyboard, on_textinput=self._on_textinput)
        return sm

    # --- Navigation ---------------------------------------------------------
    def go(self, name: str, direction: str = "left"):
        sm = self.root
        if sm.current == name:
            return
        sm.transition = SlideTransition(direction=direction, duration=0.25)
        sm.current = name

    def start_game(self, mode_key: str, level_key: str):
        if mode_key == "daily" and self.profile.daily_done():
            self.show_daily_result()
            return
        if mode_key == "classic":
            self.profile.settings["last_level"] = level_key
        game = self.root.get_screen("game")
        if self.root.current == "game":  # déjà en jeu : on repasse par l'accueil
            self.root.current = "home"
        game.start(mode_key, level_key)
        self.root.transition = FadeTransition(duration=0.25)
        self.root.current = "game"

    def show_result(self, result: dict):
        self.root.get_screen("result").show(result)
        self.root.transition = FadeTransition(duration=0.5)
        self.root.current = "result"

    def show_daily_result(self):
        Clipboard.copy(self.daily_share_text())
        toast = self.root.current_screen.ids.get("toast")
        if toast:
            toast.show("Déjà joué aujourd'hui : résultat copié, reviens demain !", "gold", 2.2)

    def daily_share_text(self) -> str:
        today = date.today().isoformat()
        daily = self.profile["modes"]["daily"]
        entry = daily["history"].get(today)
        if not entry:
            return "Pendu Royal — Défi du jour"
        feathers = "🪶" * entry["lives"] + "▪️" * (entry["max"] - entry["lives"])
        verdict = f"{entry['lives']}/{entry['max']} plumes" if entry["won"] else "pendu 💀"
        return (f"Pendu Royal — Défi du {date.today():%d/%m/%Y}\n{feathers}\n{verdict} · "
                f"{entry['errors']} erreur(s) · série {daily['streak']} 🔥")

    # --- Clavier physique / bouton retour Android ----------------------------
    def _on_keyboard(self, window, key, scancode, codepoint, modifiers):
        screen = self.root.current_screen
        if key == 27:  # Échap ou retour Android
            return screen.on_back()
        if screen.name == "game" and self._no_modal():
            kb = screen.ids.keyboard
            if key in (13, 271):
                kb.validate()
                return True
            if key == 8:
                kb.select("")
                return True
        return False

    def _on_textinput(self, window, text):
        screen = self.root.current_screen
        if screen.name != "game" or not self._no_modal():
            return
        letter = fold(text.lower())  # « é » tapé sur un clavier physique = touche « e »
        kb = screen.ids.keyboard
        if letter in kb.base_letters and not kb.locked:
            if kb.selected == letter:
                kb.validate()
            else:
                kb.select(letter)

    def _no_modal(self) -> bool:
        return not any(isinstance(w, ModalView) for w in Window.children)

    def on_pause(self):
        self.profile.save()
        return True

    def on_stop(self):
        self.profile.save()


if __name__ == "__main__":
    PenduRoyalApp().run()
