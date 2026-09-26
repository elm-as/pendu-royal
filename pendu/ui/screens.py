"""Écrans hors partie : accueil, modes, résultats, statistiques, succès, paramètres, tutoriel."""
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.properties import BooleanProperty, ColorProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen

from ..achievements import ACHIEVEMENTS
from ..config import LEVEL_ORDER, LEVELS, MODES, img
from .widgets import rgba


class BaseScreen(Screen):
    """Écran avec fond dégradé et planification Clock annulée automatiquement en quittant."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._scheduled = []

    @property
    def app(self):
        return App.get_running_app()

    def later(self, fn, delay=0.0):
        ev = Clock.schedule_once(lambda dt: fn(), delay)
        self._scheduled.append(ev)
        return ev

    def cancel_scheduled(self):
        for ev in self._scheduled:
            ev.cancel()
        self._scheduled = []

    def on_leave(self, *args):
        self.cancel_scheduled()

    def on_back(self) -> bool:
        """Touche retour Android / Échap. Renvoie False pour laisser l'app se fermer."""
        self.app.go("home", "right")
        return True


def format_duration(seconds) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}:{s:02d}"


# --- Fenêtres modales --------------------------------------------------------
class ConfirmModal(ModalView):
    title = StringProperty("")
    message = StringProperty("")
    yes_text = StringProperty("Oui")
    no_text = StringProperty("Annuler")
    on_yes = ObjectProperty(None)

    def answer(self, yes: bool):
        self.dismiss()
        if yes and self.on_yes:
            self.on_yes()


# --- Accueil -----------------------------------------------------------------
class HomeScreen(BaseScreen):
    points_text = StringProperty("")
    daily_text = StringProperty("")

    def on_pre_enter(self, *args):
        profile = self.app.profile
        self.points_text = f"{profile.points} pts"
        daily = profile["modes"]["daily"]
        if profile.daily_done():
            self.daily_text = f"Fait ! Série : {daily['streak']} jour{'s' if daily['streak'] > 1 else ''}"
        else:
            self.daily_text = "Un mot, un essai, le même pour tous"

    def play(self):
        if not self.app.profile["tutorial_done"]:
            self.app.go("tutorial", "left")
        else:
            self.app.go("modes", "left")

    def daily(self):
        if self.app.profile.daily_done():
            self.app.show_daily_result()
        else:
            self.app.start_game("daily", "medium")

    def on_back(self):
        return False


# --- Choix du mode -------------------------------------------------------------
class ModeCard(BoxLayout):
    mode_key = StringProperty("")
    title = StringProperty("")
    tagline = StringProperty("")
    record = StringProperty("")
    accent = ColorProperty(rgba("gold"))
    show_levels = BooleanProperty(False)
    level = StringProperty("noob")
    levels = ListProperty(LEVEL_ORDER)

    def level_label(self, key):
        return LEVELS[key].label

    def level_color(self, key):
        return rgba(LEVELS[key].color)

    def play(self):
        App.get_running_app().start_game(self.mode_key, self.level)


class ModesScreen(BaseScreen):
    def on_pre_enter(self, *args):
        profile = self.app.profile
        modes = profile["modes"]
        box = self.ids.cards
        box.clear_widgets()
        last_level = profile.settings.get("last_level", "noob")
        stats = profile.level_stats(last_level)
        cards = [
            ("classic", "gold", f"{LEVELS[last_level].label} : {stats['wins']} victoire(s), série {stats['streak']}"),
            ("royal", "brand", f"Record : {modes['royal']['best_words']} mot(s) · {modes['royal']['best_score']} pts"),
            ("chrono", "bonus", f"Record : {modes['chrono']['best_words']} mot(s) · {modes['chrono']['best_score']} pts"),
            ("hardcore", "danger", f"Victoires : {modes['hardcore']['wins']}"),
        ]
        for key, accent, record in cards:
            mode = MODES[key]
            box.add_widget(ModeCard(
                mode_key=key, title=mode.label, tagline=mode.tagline, record=record,
                accent=rgba(accent), show_levels=(key == "classic"), level=last_level,
            ))


# --- Résultats ------------------------------------------------------------------
class ScoreLine(BoxLayout):
    label = StringProperty("")
    value = StringProperty("")
    positive = BooleanProperty(True)


class NewAchievement(BoxLayout):
    title = StringProperty("")
    source = StringProperty("")


class ResultScreen(BaseScreen):
    title = StringProperty("")
    subtitle = StringProperty("")
    won = BooleanProperty(False)
    definition = StringProperty("")
    total_text = StringProperty("")
    points_text = StringProperty("")
    primary_text = StringProperty("REJOUER")
    header_image = StringProperty("")
    achievements = ListProperty([])

    def show(self, result: dict):
        self.result = result
        session, rnd = result["session"], result["round"]
        mode = session.mode
        self.won = rnd.won
        self.header_image = img("laurel") if rnd.won else img("pendu_dead")
        if mode.chained:
            self.title = f"{session.words_found} mot{'s' if session.words_found > 1 else ''} trouvé{'s' if session.words_found > 1 else ''}"
            self.subtitle = mode.label + (" · NOUVEAU RECORD !" if result.get("record") else "")
        elif mode.key == "daily":
            self.title = "Défi réussi !" if rnd.won else "Défi perdu…"
            self.subtitle = f"Défi du {date.today():%d/%m/%Y}"
        else:
            self.title = "Victoire !" if rnd.won else ("Abandon…" if result.get("abandon") else "Pendu !")
            self.subtitle = f"{mode.label} · {rnd.level.label}"
            if rnd.perfect:
                self.subtitle += " · PARFAIT"
        self.definition = rnd.definition
        total = session.total_score if mode.chained else result["points"]
        self.total_text = f"{total} pts"
        self.points_text = f"Bourse : {self.app.profile.points} pts"
        self.achievements = [(a.title, img(a.image)) for a in result["new_achievements"]]
        self.primary_text = "PARTAGER" if mode.key == "daily" else "REJOUER"

    def on_pre_enter(self, *args):
        lines = self.ids.lines_box
        lines.clear_widgets()
        for label, pts in self.result["breakdown"]:
            lines.add_widget(ScoreLine(label=label, value=f"+{pts}"))
        for label, pts in self.result.get("penalties", []):
            lines.add_widget(ScoreLine(label=label, value=f"-{pts}", positive=False))
        achievements = self.ids.ach_box
        achievements.clear_widgets()
        for title, source in self.achievements:
            achievements.add_widget(NewAchievement(title=title, source=source))
        board = self.ids.board
        rnd = self.result["round"]
        board.set_word(rnd.word)
        board.do_layout()
        self.ids.definition_label.text = ""
        for i, tile in enumerate(board.tiles):
            tile.opacity = 1
            self.later(lambda t=tile, r=rnd: t.reveal("shown" if r.revealed[t.index] else "missed"), 0.3 + i * 0.07)
        self._typed = 0
        self.later(self._type_definition, 0.4 + len(rnd.word) * 0.07)
        if self.result["new_achievements"]:
            self.later(lambda: self.app.audio.play("unlock"), 1.0)

    def _type_definition(self):
        """Affiche la définition progressivement (touche l'écran pour tout afficher)."""
        if self._typed >= len(self.definition):
            return
        self._typed = min(len(self.definition), self._typed + 3)
        self.ids.definition_label.text = self.definition[: self._typed]
        self.later(self._type_definition, 0.02)

    def skip_typing(self):
        self._typed = len(self.definition)
        self.ids.definition_label.text = self.definition

    def primary(self):
        session = self.result["session"]
        if session.mode.key == "daily":
            Clipboard.copy(self.app.daily_share_text())
            self.ids.toast.show("Résultat copié : colle-le à tes amis !", "gold")
        else:
            self.app.start_game(session.mode.key, session.chosen_level)


# --- Statistiques ----------------------------------------------------------------
class StatsScreen(BaseScreen):
    tab = StringProperty("noob")
    items = ListProperty([])

    def on_pre_enter(self, *args):
        self.show_tab(self.tab)

    def show_tab(self, tab: str):
        self.tab = tab
        p = self.app.profile
        if tab in LEVELS:
            s = p.level_stats(tab)
            rate = f"{100 * s['wins'] / s['games']:.0f} %" if s["games"] else "—"
            self.items = [
                ("Parties", s["games"]), ("Victoires", s["wins"]), ("Taux de victoire", rate),
                ("Série actuelle", s["streak"]), ("Meilleure série", s["best_streak"]),
                ("Victoires parfaites", s["perfect"]), ("Victoires à 1 plume", s["clutch"]),
                ("Meilleur temps", format_duration(s["best_time"])), ("Meilleur score", s["best_score"]),
                ("Indices utilisés", s["hints_used"]),
            ]
        else:
            m, t = p["modes"], p["totals"]
            self.items = [
                ("Royal : record", f"{m['royal']['best_words']} mots"), ("Royal : meilleur score", m["royal"]["best_score"]),
                ("Chrono : record", f"{m['chrono']['best_words']} mots"), ("Chrono : meilleur score", m["chrono"]["best_score"]),
                ("Sans filet : victoires", m["hardcore"]["wins"]), ("Défi du jour : série", m["daily"]["streak"]),
                ("Défi : meilleure série", m["daily"]["best_streak"]), ("Défis réussis", f"{m['daily']['wins']} / {m['daily']['played']}"),
                ("Mots différents trouvés", len(p["found_words"])), ("Points gagnés", t["points_earned"]),
            ]
        grid = self.ids.grid
        grid.clear_widgets()
        for label, value in self.items:
            grid.add_widget(StatCard(label=label, value=str(value)))


class StatCard(BoxLayout):
    label = StringProperty("")
    value = StringProperty("")


# --- Succès ------------------------------------------------------------------------
class AchievementCard(BoxLayout):
    title = StringProperty("")
    description = StringProperty("")
    source = StringProperty("")
    unlocked = BooleanProperty(False)
    date_text = StringProperty("")


class AchievementsScreen(BaseScreen):
    counter = StringProperty("")

    def on_pre_enter(self, *args):
        unlocked = self.app.profile["achievements"]
        grid = self.ids.grid
        grid.clear_widgets()
        for a in ACHIEVEMENTS:
            day = unlocked.get(a.key)
            grid.add_widget(AchievementCard(
                title=a.title, description=a.description, source=img(a.image), unlocked=bool(day),
                date_text=f"Obtenu le {date.fromisoformat(day):%d/%m/%Y}" if day else "Verrouillé",
            ))
        self.counter = f"{len(unlocked)} / {len(ACHIEVEMENTS)}"


# --- Paramètres ------------------------------------------------------------------
class SettingsScreen(BaseScreen):
    sound = BooleanProperty(True)
    vibration = BooleanProperty(True)

    def on_pre_enter(self, *args):
        s = self.app.profile.settings
        self.sound, self.vibration = s["sound"], s["vibration"]

    def toggle(self, name: str):
        s = self.app.profile.settings
        s[name] = not s[name]
        setattr(self, name, s[name])
        self.app.profile.save()

    def replay_tutorial(self):
        self.app.go("tutorial", "left")

    def reset(self):
        def do_reset():
            self.app.profile.reset_stats()
            self.app.profile.save()
            self.ids.toast.show("Statistiques réinitialisées.", "gold")
        ConfirmModal(title="Tout effacer ?", message="Statistiques, succès, séries et points seront remis à zéro.",
                     yes_text="Effacer", on_yes=do_reset).open()


# --- Tutoriel ------------------------------------------------------------------------
TUTORIAL = (
    ("Bienvenue au Pendu Royal", "Trouve le mot caché lettre par lettre avant de perdre tes plumes. "
     "Chaque plume perdue ajoute une pièce à la potence… et rapproche le roi de sa fin.", "pendu_hero"),
    ("Jouer une lettre", "Touche une lettre pour la sélectionner, puis VALIDER (ou touche-la une seconde fois). "
     "Pas besoin d'accents : « e » révèle aussi é, è, ê. "
     "Les lettres trouvées deviennent vertes, les ratées se grisent.", "f1"),
    ("Le temps presse", "Chaque tour est chronométré. Si le temps s'écoule, tu perds une plume. "
     "Chaque lettre validée relance le chrono.", "time_pressure"),
    ("Événements", "En Corsé et en Infernal, des événements surgissent : clavier fou, mot miroir, "
     "ruée vers l'or, seconde chance… Lis bien leur description !", "gold_run"),
    ("Indices et mot entier", "Dépense tes points pour un indice (lettre, thème, définition…). "
     "Tu peux aussi tenter le mot entier : gros bonus, mais une erreur coûte 2 plumes.", "perfect"),
    ("Relève le défi", "Mode Royal, Contre-la-montre, Sans filet et Défi du jour t'attendent. "
     "Neuf succès sont à débloquer. Bonne chance !", "RG_1_m_1"),
)


class TutorialScreen(BaseScreen):
    page = ObjectProperty(0)
    heading = StringProperty("")
    body = StringProperty("")
    picture = StringProperty("")
    pages = len(TUTORIAL)

    def on_pre_enter(self, *args):
        self.set_page(0)

    def set_page(self, page: int):
        self.page = page
        self.heading, self.body, picture = TUTORIAL[page]
        self.picture = img(picture)

    def next(self):
        if self.page + 1 < len(TUTORIAL):
            self.set_page(self.page + 1)
        else:
            self.finish()

    def finish(self):
        self.app.profile.data["tutorial_done"] = True
        self.app.profile.save()
        self.app.go("modes", "left")
