"""Composants visuels réutilisables. Leur apparence est décrite dans pendu.kv."""
import json
import math

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty, ColorProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.layout import Layout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from ..config import ASSETS, COLORS, KEYBOARD_ROWS, img


def rgba(name_or_hex: str, alpha: float = 1.0) -> list:
    color = get_color_from_hex(COLORS.get(name_or_hex, name_or_hex))
    color[3] = alpha
    return color


def shade(color, factor: float) -> list:
    return [min(1.0, c * factor) for c in color[:3]] + [color[3]]


def vertical_gradient(top: str, bottom: str, steps: int = 64) -> Texture:
    t, b = rgba(top), rgba(bottom)
    buf = bytearray()
    for i in range(steps):  # de bas en haut
        k = i / (steps - 1)
        buf += bytes(int(255 * (b[c] + (t[c] - b[c]) * k)) for c in range(3)) + b"\xff"
    tex = Texture.create(size=(1, steps), colorfmt="rgba")
    tex.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
    return tex


class RoundButton(ButtonBehavior, Label):
    """Bouton arrondi qui s'enfonce légèrement au toucher."""
    bg = ColorProperty(rgba("brand"))
    fg = ColorProperty(rgba("text"))
    radius = NumericProperty(dp(14))
    scale = NumericProperty(1.0)
    sound = StringProperty("click")

    def on_press(self):
        Animation.cancel_all(self, "scale")
        Animation(scale=0.93, d=0.06).start(self)
        app = App.get_running_app()
        if self.sound and app:
            app.audio.play(self.sound)

    def on_release(self):
        Animation(scale=1.0, d=0.12, t="out_back").start(self)


class Panel(BoxLayout):
    bg = ColorProperty(rgba("panel"))
    border = ColorProperty(rgba("border"))
    radius = NumericProperty(dp(16))


class LetterTile(Label):
    """Case d'une lettre du mot, qui se retourne quand la lettre est trouvée."""
    letter = StringProperty("")
    shown = BooleanProperty(False)
    state = StringProperty("hidden")  # hidden, shown, fresh, missed
    flip = NumericProperty(1.0)
    index = NumericProperty(0)

    def reveal(self, state="fresh", delay=0.0):
        def go(*_):
            anim = Animation(flip=0.0, d=0.11, t="in_quad")
            anim.bind(on_complete=lambda *a: self._show(state))
            anim.start(self)
        Clock.schedule_once(go, delay) if delay else go()

    def _show(self, state):
        self.shown = True
        self.state = state
        Animation(flip=1.0, d=0.14, t="out_back").start(self)
        if state == "fresh":
            Clock.schedule_once(lambda *_: setattr(self, "state", "shown") if self.state == "fresh" else None, 0.9)


class WordBoard(Layout):
    """Dispose les lettres sur une seule ligne (un mot = une ligne), ordre d'affichage modifiable."""
    order = ListProperty([])
    tile_size = NumericProperty(dp(40))
    offset_x = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tiles = []
        self._animate = False
        self.bind(size=self._trigger_layout, pos=self._trigger_layout,
                  order=self._trigger_layout, offset_x=self._trigger_layout)

    def set_word(self, word: str):
        self.clear_widgets()
        self.tiles = []
        for i, ch in enumerate(word):
            tile = LetterTile(letter=ch, index=i, opacity=0)
            self.tiles.append(tile)
            self.add_widget(tile)
        self.order = list(range(len(word)))

    def set_order(self, order, animate=True):
        self._animate = animate
        self.order = list(order) if order else list(range(len(self.tiles)))

    def do_layout(self, *args):
        n = len(self.tiles)
        if not n:
            return
        gap = dp(5) if n <= 9 else dp(3)
        width = (self.width - (n - 1) * gap) / n
        height = min(self.height, width * 1.25, dp(58))  # cases un peu plus hautes que larges si le mot est long
        width = min(width, height)
        self.tile_size = width
        x0 = self.center_x - (n * width + (n - 1) * gap) / 2
        y = self.center_y - height / 2
        for slot, tile_index in enumerate(self.order):
            tile = self.tiles[tile_index]
            x = x0 + slot * (width + gap) + self.offset_x
            tile.size = (width, height)
            if self._animate:
                Animation(pos=(x, y), d=0.35, t="out_quad").start(tile)
            else:
                tile.pos = (x, y)
        self._animate = False

    def shake(self):
        anim = Animation(offset_x=dp(-10), d=0.05) + Animation(offset_x=dp(9), d=0.07)
        anim += Animation(offset_x=dp(-6), d=0.07) + Animation(offset_x=0, d=0.06)
        anim.start(self)


class KeyButton(RoundButton):
    letter = StringProperty("")
    status = StringProperty("")  # "", selected, hit, miss  (« state » est pris par ButtonBehavior)


class Keyboard(BoxLayout):
    """Clavier AZERTY : une touche sélectionne, VALIDER (ou re-toucher la touche) confirme."""
    selected = StringProperty("")
    on_validate = ObjectProperty(None)
    locked = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(orientation="vertical", spacing=dp(6), **kw)
        self.keys = []
        self.state_for = lambda letter: ""
        for r, row in enumerate(KEYBOARD_ROWS):
            line = BoxLayout(spacing=dp(4))
            if r == len(KEYBOARD_ROWS) - 1:
                line.add_widget(Widget(size_hint_x=0.5))
            for letter in row:
                key = KeyButton(letter=letter, text=letter, sound="select")
                key.bind(on_release=self._tap)
                self.keys.append(key)
                line.add_widget(key)
            if r == len(KEYBOARD_ROWS) - 1:
                self.validate_button = RoundButton(text="VALIDER", size_hint_x=3.5, bg=rgba("gold"),
                                                   fg=rgba("ink"), bold=True, sound="")
                self.validate_button.bind(on_release=lambda *_: self.validate())
                line.add_widget(self.validate_button)
            self.add_widget(line)
        self.base_letters = [k.letter for k in self.keys]

    def _tap(self, key):
        if self.locked or key.status in ("hit", "miss"):
            return
        if self.selected == key.letter:
            self.validate()
        else:
            self.select(key.letter)

    def select(self, letter: str):
        if self.locked:
            return
        self.selected = letter
        self.refresh()

    def validate(self):
        if self.locked or not self.selected:
            return
        letter, self.selected = self.selected, ""
        if self.on_validate:
            self.on_validate(letter)
        self.refresh()

    def refresh(self):
        for key in self.keys:
            state = self.state_for(key.letter)
            key.status = state or ("selected" if key.letter == self.selected else "")
            key.disabled = state == "miss"
        self.validate_button.opacity = 1.0 if self.selected else 0.55

    def shuffle(self, active: bool, rng):
        letters = list(self.base_letters)
        if active:
            rng.shuffle(letters)
        for key, letter in zip(self.keys, letters):
            if key.letter != letter:
                key.letter = key.text = letter
                key.scale = 0.6
                Animation(scale=1.0, d=0.25, t="out_back").start(key)
        self.refresh()


class Feather(Image):
    drop = NumericProperty(0)
    angle = NumericProperty(0)


class FeatherBar(BoxLayout):
    """Les plumes = les vies. Une plume perdue tombe en tournoyant."""

    def setup(self, max_lives: int, lives: int):
        self.clear_widgets()
        self.feathers = []
        for i in range(max_lives):
            f = Feather(source=img(f"f{i % 9 + 1}"), fit_mode="contain")
            f.opacity = 1.0 if i < lives else 0.0
            self.feathers.append(f)
            self.add_widget(f)

    def set_lives(self, lives: int):
        for i, f in enumerate(self.feathers):
            alive = i < lives
            if alive and f.opacity < 1:
                f.drop, f.angle = dp(-30), 0
                Animation(opacity=1, drop=0, d=0.4, t="out_back").start(f)
            elif not alive and f.opacity > 0 and f.drop == 0:
                anim = Animation(drop=dp(70), angle=-50, opacity=0, d=0.8, t="in_quad")
                anim.bind(on_complete=lambda _a, w: setattr(w, "drop", 0))
                anim.start(f)


class Gallows(RelativeLayout):
    """Le pendu royal, dessiné pièce par pièce (images générées par tools/make_hangman.py).

    stage 0 à 9 : nombre de pièces visibles. Les pièces à venir restent en filigrane.
    """
    stage = NumericProperty(0)
    mood = StringProperty("calm")  # calm, worry, dead
    GHOST = 0.06
    STEPS = 9
    _layout_data = None

    def __init__(self, **kw):
        super().__init__(**kw)
        if Gallows._layout_data is None:
            with open(ASSETS / "images" / "pendu_layout.json", encoding="utf-8") as fh:
                Gallows._layout_data = json.load(fh)
        data = Gallows._layout_data
        self.layers = []
        for layer in data["layers"]:
            im = Image(source=img(layer["name"]), fit_mode="fill", size_hint=(None, None), opacity=self.GHOST)
            self.layers.append((layer["stage"], layer["box"], im))
            self.add_widget(im)
            if layer["name"] == data["face_after"]:
                self.faces = {}
                for mood, box in data["faces"].items():
                    face = Image(source=img(f"pendu_face_{mood}"), fit_mode="fill", size_hint=(None, None), opacity=0)
                    self.faces[mood] = (box, face)
                    self.add_widget(face)
        self.bind(size=self._place)
        self.apply(animate=False)

    def _place(self, *_):
        side = min(self.width, self.height)
        ox, oy = (self.width - side) / 2, (self.height - side) / 2  # coordonnées locales
        items = [(box, im) for _s, box, im in self.layers] + list(self.faces.values())
        for (bx, by, bw, bh), im in items:
            im.pos = (ox + bx * side, oy + by * side)
            im.size = (bw * side, bh * side)

    def set_progress(self, lost: int, max_lives: int, dead: bool = False):
        stage = 0 if max_lives <= 0 else math.ceil(lost / max_lives * self.STEPS)
        self.stage = min(self.STEPS, stage)
        self.mood = "dead" if dead else ("worry" if self.stage >= 7 else "calm")

    def on_stage(self, *_):
        self.apply()

    def on_mood(self, *_):
        self.apply()

    def apply(self, animate=True):
        for stage, _box, im in self.layers:
            # seule la potence (étapes 1 à 5) reste en filigrane ; le roi n'apparaît qu'une fois « dessiné »
            ghost = self.GHOST if stage <= 5 else 0.0
            target = 1.0 if stage <= self.stage else ghost
            if im.opacity != target:
                Animation.cancel_all(im)
                if animate and target == 1.0:
                    Animation(opacity=1.0, d=0.35, t="out_quad").start(im)
                else:
                    im.opacity = target
        head_visible = self.stage >= 6
        for mood, (_box, face) in self.faces.items():
            face.opacity = 1.0 if head_visible and mood == self.mood else 0.0


class TimerRing(FloatLayout):
    """Minuteur circulaire. progress = part de temps restant."""
    progress = NumericProperty(1.0)
    text = StringProperty("")
    hidden = BooleanProperty(False)
    danger = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self.redraw, pos=self.redraw, progress=self.redraw, hidden=self.redraw, danger=self.redraw)

    def redraw(self, *_):
        self.canvas.before.clear()
        r = min(self.width, self.height) / 2 * 0.86
        cx, cy = self.center
        with self.canvas.before:
            Color(*rgba("panel"))
            Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))
            Color(*rgba("border"))
            Line(circle=(cx, cy, r), width=dp(3))
            if not self.hidden:
                Color(*rgba("danger" if self.danger else "gold"))
                Line(circle=(cx, cy, r, 0, 360 * max(0.0, min(1.0, self.progress))), width=dp(3.2), cap="round")


class Toast(Label):
    """Petit message éphémère au-dessus du clavier."""

    def show(self, text: str, color="text", duration=1.4):
        Animation.cancel_all(self)
        self.text = text
        self.color = rgba(color)
        self.opacity = 0
        anim = Animation(opacity=1, d=0.15) + Animation(d=duration) + Animation(opacity=0, d=0.3)
        anim.start(self)
