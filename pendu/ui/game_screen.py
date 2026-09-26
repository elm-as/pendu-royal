"""Écran de partie : relie la logique (Session/Round/événements) à l'affichage.

Un seul Clock.schedule_interval fait avancer le temps. Toutes les
temporisations passent par self.later() et sont annulées en quittant l'écran,
ce qui évite les callbacks « fantômes » d'une partie à l'autre.
"""
import math
import random
import time

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import (
    BooleanProperty, ColorProperty, NumericProperty, ObjectProperty, StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView

from ..achievements import unlock_new
from ..config import HINTS, img
from ..events import EventDirector, roll_event
from ..game import ALREADY, HIT, MISS, SHIELDED, Session
from ..words import mask_definition
from .screens import BaseScreen, ConfirmModal
from .widgets import rgba

CHRONO_SKIP_COST = 10


class GameScreen(BaseScreen):
    title = StringProperty("")
    subtitle = StringProperty("")
    level_color = ColorProperty(rgba("gold"))
    score_text = StringProperty("")
    points_text = StringProperty("")
    timer_text = StringProperty("")
    hint_text = StringProperty("")
    combo_text = StringProperty("")
    chrono = BooleanProperty(False)
    unlimited = BooleanProperty(False)
    hints_enabled = BooleanProperty(True)
    hints_locked = BooleanProperty(False)
    # Bandeau d'événement
    event_visible = BooleanProperty(False)
    event_name = StringProperty("")
    event_desc = StringProperty("")
    event_image = StringProperty("")
    event_color = ColorProperty(rgba("penalty"))
    event_progress = NumericProperty(1.0)
    banner_x = NumericProperty(1.0)   # 0 = bandeau visible, 1 = hors écran à droite

    def __init__(self, **kw):
        super().__init__(**kw)
        self.session = None
        self.round = None
        self.director = None
        self.phase = "idle"
        self.rng = random.Random()
        self._clock = None
        self._last_tick_second = None
        self.paused_by_modal = False

    # --- Démarrage ---------------------------------------------------------
    def start(self, mode_key: str, level_key: str):
        app = self.app
        self.session = Session(mode_key, level_key, app.bank, recent=app.profile["recent_words"], rng=self.rng)
        self.chrono = bool(self.session.mode.global_time)
        self.unlimited = self.chrono
        self.hints_enabled = self.session.mode.hints

    def on_enter(self, *args):
        kb = self.ids.keyboard
        kb.on_validate = self.guess_letter
        self._clock = Clock.schedule_interval(self._tick, 1 / 30)
        self.begin_round()

    def on_leave(self, *args):
        super().on_leave(*args)
        if self._clock:
            self._clock.cancel()
            self._clock = None
        if self.director:
            self.director.end(self)
        self.phase = "idle"
        Animation.cancel_all(self)

    def begin_round(self):
        session = self.session
        rnd = self.round = session.next_round()
        boss = session.is_boss()
        self.director = EventDirector(rnd.level, self.rng, boss=boss)
        self.time_scale = 1.0
        self.turn_time = session.turn_time(rnd.level)
        self.remaining = float(self.turn_time)
        self.started_at = time.time()
        self.phase = "intro"
        self.hints_locked = False
        self.hint_text = ""
        self.combo_text = ""
        self.event_visible = False
        self.banner_x = 1.0
        self.set_timer_hidden(False)

        mode = session.mode
        self.title = f"{mode.label} · {rnd.level.label}" if not mode.chained else mode.label
        self.level_color = rgba(rnd.level.color)
        if mode.chained:
            self.subtitle = f"Mot {session.index} · {rnd.level.label}" + (" · BOSS" if boss else "")
        elif mode.key == "daily":
            self.subtitle = "Un seul essai aujourd'hui"
        else:
            self.subtitle = f"{len(rnd.word)} lettres"
        self._update_texts()

        board = self.ids.board
        board.set_word(rnd.word)
        kb = self.ids.keyboard
        kb.state_for = rnd.key_state
        kb.selected = ""
        kb.shuffle(False, self.rng)
        kb.locked = True
        feathers = self.ids.feathers
        feathers.setup(rnd.max_lives, rnd.lives)
        self.ids.gallows.set_progress(rnd.max_lives - rnd.lives, rnd.max_lives)
        self._update_timer()

        if boss:
            self.ids.toast.show("BOSS ! Un événement t'attend…", "danger", 1.8)
        for i, tile in enumerate(board.tiles):
            tile.opacity = 0
            self.later(lambda t=tile: Animation(opacity=1, d=0.2).start(t), 0.05 * i)
        start_delay = 0.05 * len(board.tiles) + 0.2
        ratio = rnd.level.reveal_ratio if mode.reveal_letters else 0
        revealed = rnd.reveal_start(ratio, self.rng)
        for k, pos in enumerate(revealed):
            self.later(lambda p=pos: board.tiles[p].reveal("shown"), start_delay + 0.12 * k)
        self.later(self._start_play, start_delay + 0.12 * len(revealed) + 0.2)

    def _start_play(self):
        if self.phase != "intro":
            return
        self.phase = "play"
        self.ids.keyboard.locked = False
        self.ids.keyboard.refresh()
        self.director.new_turn(self.turn_time)
        if self.session.is_boss():
            self.later(lambda: self._announce(roll_event(self.rng, kind="penalty")), 0.6)

    # --- Boucle de temps -----------------------------------------------------
    def _tick(self, dt):
        if self.phase != "play" or self.paused_by_modal:
            return
        if self.chrono:
            self.session.time_left -= dt
            if self.session.time_left <= 0:
                self.session.time_left = 0
                self._update_timer()
                self.ids.toast.show("Temps écoulé !", "danger")
                self.end_round()
                return
        elif self.turn_time:
            self.remaining -= dt * self.time_scale
            event = self.director.check(self.remaining)
            if event:
                self._announce(event)
                return
            if self.remaining <= 0:
                self._on_timeout()
                return
        if self.director.tick(dt, self):
            self._event_ended()
        self.event_progress = self.director.progress()
        self._update_timer()

    def _update_timer(self):
        ring = self.ids.timer
        if self.chrono:
            left = max(0.0, self.session.time_left)
            ring.progress = left / self.session.mode.global_time
            # en contre-la-montre, la potence se construit au fil du temps écoulé
            total = self.session.mode.global_time
            self.ids.gallows.set_progress(total - left, total, dead=left <= 0)
            m, s = divmod(int(math.ceil(left)), 60)
            self.timer_text = f"{m}:{s:02d}"
            ring.danger = left <= 20
            return
        if not self.turn_time:
            ring.progress, self.timer_text = 1.0, ""
            return
        left = max(0.0, self.remaining)
        ring.progress = left / self.turn_time
        seconds = int(math.ceil(left))
        ring.danger = seconds <= 5
        self.timer_text = "?" if ring.hidden else str(seconds)
        if self.phase == "play" and seconds <= 5 and seconds != self._last_tick_second and not ring.hidden:
            self._last_tick_second = seconds
            self.app.audio.play("tick")

    def _on_timeout(self):
        res = self.round.timeout()
        self._apply_miss(res, "Temps écoulé ! Une plume s'envole.")
        if res.lost:
            self.end_round()
        else:
            self._new_turn()

    def _new_turn(self):
        if self.director.end_turn(self):
            self._event_ended()
        self.remaining = float(self.turn_time)
        self._last_tick_second = None
        self.director.new_turn(self.turn_time)

    # --- Actions du joueur ---------------------------------------------------
    def guess_letter(self, letter: str):
        if self.phase != "play":
            return
        rnd = self.round
        res = rnd.guess(letter)
        if res.kind == ALREADY:
            self.ids.toast.show("Lettre déjà jouée.", "muted")
            return
        if res.kind == HIT:
            self._reveal(res.positions)
            self.app.audio.play("hit")
            if rnd.combo >= 3:
                self.combo_text = f"Combo x{rnd.combo}"
                self.ids.toast.show(f"Combo x{rnd.combo} !", "gold", 0.9)
            if rnd.gold_per_tile:
                self.ids.toast.show(f"+{rnd.gold_per_tile * len(res.positions)} pts d'or !", "gold", 0.9)
        elif res.kind == SHIELDED:
            self.app.audio.play("coin")
            self.ids.toast.show("Seconde chance : erreur annulée !", "bonus")
        else:
            self.combo_text = ""
            self._apply_miss(res)
        self.ids.keyboard.refresh()
        self._update_texts()
        if res.won or res.lost:
            self.end_round()
        else:
            self._new_turn()

    def _reveal(self, positions):
        tiles = self.ids.board.tiles
        for k, p in enumerate(positions):
            tiles[p].reveal("fresh", delay=0.07 * k)

    def _apply_miss(self, res, message="Raté !"):
        rnd = self.round
        self.app.audio.play("miss")
        self.app.audio.vibrate(80)
        self.ids.board.shake()
        if res.lives_lost:
            self.later(lambda: self.app.audio.play("feather"), 0.15)
        self.ids.feathers.set_lives(rnd.lives)
        self.ids.gallows.set_progress(rnd.max_lives - rnd.lives, rnd.max_lives)
        if self.chrono:
            self.session.chrono_penalty()
            message = "Raté ! -5 secondes"
        if rnd.tax_per_miss:
            message += f"  L'impôt du roi : -{rnd.tax_per_miss} pts"
        self.ids.toast.show(message, "danger")

    def open_hints(self):
        if self.phase != "play":
            return
        if not self.hints_enabled:
            self.ids.toast.show("Pas d'indice en mode Sans filet !", "danger")
            return
        if self.hints_locked:
            self.ids.toast.show("Tour glacial : indices gelés !", "bonus")
            return
        HintModal(screen=self).open()

    def use_hint(self, kind: str):
        label, cost = HINTS[kind]
        rnd = self.round
        if self.phase != "play":
            return
        if not self.app.profile.spend(cost):
            self.ids.toast.show("Pas assez de points.", "danger")
            return
        self.app.audio.play("coin")
        if kind == "letter":
            positions = rnd.hint_letter(self.rng)
            self._reveal(positions)
            self.ids.keyboard.refresh()
            if rnd.won:
                self.end_round()
                return
        elif kind == "eliminate":
            gone = rnd.hint_eliminate(3, self.rng)
            self.ids.keyboard.refresh()
            self.ids.toast.show("Absentes : " + ", ".join(g.upper() for g in gone), "gold")
        elif kind == "theme":
            rnd.note_hint("theme")
            self.hint_text = f"Thème : {rnd.theme}"
        elif kind == "definition":
            rnd.note_hint("definition")
            self.hint_text = mask_definition(rnd.definition, rnd.word)
        self._update_texts()

    def open_word_guess(self):
        if self.phase != "play":
            return
        WordGuessModal(screen=self).open()

    def guess_word(self, text: str):
        if self.phase != "play" or not text.strip():
            return
        res = self.round.guess_word(text)
        if res.kind == HIT:
            self._reveal(res.positions)
            self.app.audio.play("hit")
            self.ids.toast.show("Bien vu !", "gold")
            self.ids.keyboard.refresh()
            self.end_round()
            return
        if res.kind == SHIELDED:
            self.ids.toast.show("Seconde chance : erreur annulée !", "bonus")
        else:
            self._apply_miss(res, f"Ce n'est pas « {text.strip()} ». -{res.lives_lost} plumes")
        self._update_texts()
        if res.lost:
            self.end_round()
        else:
            self._new_turn()

    def skip_word(self):
        """Contre-la-montre : passer le mot coûte 10 secondes."""
        if self.phase != "play" or not self.chrono:
            return
        self.session.time_left = max(0.0, self.session.time_left - CHRONO_SKIP_COST)
        self.ids.toast.show(f"Mot passé : -{CHRONO_SKIP_COST} secondes", "muted")
        self.end_round()

    def on_back(self):
        if self.phase in ("play", "intro", "paused") and not self.paused_by_modal:
            self.paused_by_modal = True
            modal = ConfirmModal(title="Abandonner ?", message="La partie sera comptée comme une défaite.",
                                 yes_text="Abandonner", on_yes=lambda: self.end_round(abandon=True))
            modal.bind(on_dismiss=lambda *_: setattr(self, "paused_by_modal", False))
            modal.open()
        return True

    # --- Événements --------------------------------------------------------------
    def _announce(self, event):
        """Présente l'événement (timer en pause), puis l'active."""
        if self.phase != "play":
            return
        info = event.info
        self.phase = "paused"
        self.ids.keyboard.locked = True
        self.event_name = info.name
        self.event_desc = info.description
        self.event_image = img(info.key)
        self.event_color = rgba("bonus" if info.kind == "bonus" else "penalty")
        self.event_progress = 1.0
        self.event_visible = True
        self.app.audio.play("event")
        Animation.cancel_all(self, "banner_x")
        Animation(banner_x=0.0, d=0.35, t="out_back").start(self)

        def activate():
            if self.phase != "paused":
                return
            if self.paused_by_modal:  # confirmation d'abandon ouverte : on attend
                self.later(activate, 0.3)
                return
            self.director.begin(event, self)
            self.phase = "play"
            self.ids.keyboard.locked = False
            self.ids.keyboard.refresh()
        self.later(activate, 1.8)

    def _event_ended(self):
        Animation(banner_x=1.0, d=0.3, t="in_quad").start(self)
        self.later(lambda: setattr(self, "event_visible", False) if self.director.active is None else None, 0.35)

    # Interface utilisée par pendu.events (ctx)
    def set_time_scale(self, scale):
        self.time_scale = scale

    def set_timer_hidden(self, hidden):
        self.ids.timer.hidden = hidden
        self._update_timer()

    def set_tile_order(self, order):
        self.ids.board.set_order(order, animate=True)

    def shuffle_keyboard(self, active):
        self.ids.keyboard.shuffle(active, self.rng)

    def set_hints_locked(self, locked):
        self.hints_locked = locked

    # --- Fin de manche --------------------------------------------------------------
    def _update_texts(self):
        profile = self.app.profile
        self.points_text = f"{profile.points} pts"
        self.score_text = f"Score {self.session.total_score}" if self.session.mode.chained else ""

    def end_round(self, abandon=False):
        if self.phase in ("end", "idle"):
            return
        self.phase = "end"
        self.cancel_scheduled()  # animations d'intro, activation d'événement en attente…
        kb = self.ids.keyboard
        kb.locked = True
        kb.selected = ""
        if self.director.end(self):
            self._event_ended()
        self.ids.board.set_order(None, animate=True)
        kb.shuffle(False, self.rng)
        self.set_timer_hidden(False)

        rnd, session, profile = self.round, self.session, self.app.profile
        for tile in self.ids.board.tiles:
            tile.opacity = 1
            if not tile.shown:
                state = "shown" if rnd.revealed[tile.index] else "missed"
                tile.reveal(state, delay=0.3 + 0.05 * tile.index)
        self.app.audio.play("win" if rnd.won else "lose")
        if not rnd.won:
            self.app.audio.vibrate(300)
            if not self.chrono:
                self.ids.gallows.set_progress(rnd.max_lives, rnd.max_lives, dead=True)

        breakdown = rnd.score_breakdown(session.extra_score(rnd))
        points = session.finish_round(rnd)
        if abandon:
            session.over = True
        penalties = []
        if rnd.tax_paid:
            penalties.append(("L'impôt du roi", rnd.tax_paid))
            profile.pay(rnd.tax_paid)
        if rnd.double_or_nothing and not rnd.won:
            penalties.append(("Quitte ou double perdu", 20))
            profile.pay(20)
        profile.record_round(rnd, points, time.time() - self.started_at,
                             count_level_stats=(session.mode.key == "classic"))
        self._update_texts()

        if not session.over:
            profile.save()
            if rnd.won:
                self.ids.toast.show(f"Mot trouvé ! +{points} pts", "gold", 1.2)
            self.later(self.begin_round, 1.8)
            return

        best_before = dict(profile["modes"].get(session.mode.key, {}))
        profile.record_session(session)
        record = session.mode.chained and session.total_score > best_before.get("best_score", 0)
        new_achievements = unlock_new(profile.data, session)
        profile.save()
        result = {
            "session": session, "round": rnd, "points": points, "breakdown": breakdown,
            "penalties": penalties, "new_achievements": new_achievements, "abandon": abandon,
            "record": record,
        }
        self.later(lambda: self.app.show_result(result), 0.5 if abandon else 1.8)


# --- Fenêtres modales de la partie -------------------------------------------------
class HintModal(ModalView):
    """Le chrono continue pendant le choix : pas de pause gratuite pour réfléchir."""
    screen = ObjectProperty(None)

    def on_open(self):
        screen = self.screen
        rnd = screen.round
        points = screen.app.profile.points
        box = self.ids.options
        box.clear_widgets()
        descriptions = {
            "letter": "Révèle une lettre du mot.",
            "eliminate": "Grise 3 lettres absentes du mot.",
            "theme": "Affiche le thème du mot.",
            "definition": "Affiche la définition (le mot y est masqué).",
        }
        for kind, (label, cost) in HINTS.items():
            available = True
            if kind == "theme" and (not rnd.theme or "theme" in rnd.hints_used):
                available = False
            if kind == "definition" and (not rnd.definition or "definition" in rnd.hints_used):
                available = False
            if kind == "letter" and rnd.hidden_count() <= 1:
                available = False
            box.add_widget(HintOption(
                kind=kind, label=label, cost=cost, description=descriptions[kind],
                enabled=available and points >= cost, modal=self,
            ))
        self.ids.wallet.text = f"Ta bourse : {points} pts"

    def choose(self, kind):
        self.dismiss()
        self.screen.use_hint(kind)


class HintOption(BoxLayout):
    kind = StringProperty("")
    label = StringProperty("")
    cost = NumericProperty(0)
    description = StringProperty("")
    enabled = BooleanProperty(True)
    modal = ObjectProperty(None)


class WordGuessModal(ModalView):
    """Proposer le mot entier. Le chrono continue pendant la saisie."""
    screen = ObjectProperty(None)

    def on_open(self):
        Clock.schedule_once(lambda dt: setattr(self.ids.entry, "focus", True), 0.1)

    def submit(self, text):
        self.dismiss()
        self.screen.guess_word(text)
