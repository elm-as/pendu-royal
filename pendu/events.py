"""Événements aléatoires en cours de partie.

Chaque événement agit sur la partie via une petite interface (`ctx`) exposée
par l'écran de jeu :
    ctx.round                 la manche en cours (pendu.game.Round)
    ctx.set_time_scale(x)     vitesse d'écoulement du timer (1 = normal)
    ctx.set_timer_hidden(b)
    ctx.set_tile_order(o)     ordre d'affichage des lettres (None = normal)
    ctx.shuffle_keyboard(b)
    ctx.set_hints_locked(b)
Un événement est donc testable sans Kivy avec un faux ctx.
"""
import random
from dataclasses import dataclass

TURN = "turn"     # dure jusqu'à la fin du tour (prochaine lettre validée ou temps écoulé)
ROUND = "round"   # dure jusqu'à la fin du mot
UNTIL = "until"   # dure jusqu'à ce que `finished(ctx)` soit vrai (ou fin du mot)

RARITY_WEIGHTS = (("common", 0.64), ("rare", 0.30), ("epic", 0.06))
BONUS_CHANCE = 0.45


@dataclass(frozen=True)
class EventInfo:
    key: str
    name: str
    kind: str        # "bonus" ou "penalty"
    rarity: str
    duration: object  # secondes (float) ou TURN / ROUND / UNTIL
    description: str


class Event:
    info: EventInfo

    def start(self, ctx):
        pass

    def stop(self, ctx):
        pass

    def finished(self, ctx) -> bool:
        return False


class MirrorLetter(Event):
    info = EventInfo("mirror_letter", "Lettres miroir", "penalty", "common", 10,
                     "Le mot s'affiche à l'envers pendant 10 secondes.")

    def start(self, ctx):
        ctx.set_tile_order(list(reversed(range(len(ctx.round.word)))))

    def stop(self, ctx):
        ctx.set_tile_order(None)


class RandomScrambleFlask(Event):
    info = EventInfo("random_scramble_flask", "Fiole du chaos", "penalty", "rare", 15,
                     "Les lettres du mot sont mélangées pendant 15 secondes.")

    def start(self, ctx):
        order = list(range(len(ctx.round.word)))
        while len(order) > 1 and order == sorted(order):
            random.shuffle(order)
        ctx.set_tile_order(order)

    def stop(self, ctx):
        ctx.set_tile_order(None)


class LetterShuffle(Event):
    info = EventInfo("letter_shuffle", "Clavier fou", "penalty", "rare", 15,
                     "Les touches du clavier changent de place pendant 15 secondes.")

    def start(self, ctx):
        ctx.shuffle_keyboard(True)

    def stop(self, ctx):
        ctx.shuffle_keyboard(False)


class HiddenTimer(Event):
    info = EventInfo("hidden_timer", "Sablier voilé", "penalty", "common", 10,
                     "Le timer devient invisible pendant 10 secondes.")

    def start(self, ctx):
        ctx.set_timer_hidden(True)

    def stop(self, ctx):
        ctx.set_timer_hidden(False)


class TimePressure(Event):
    info = EventInfo("time_pressure", "Pression du temps", "penalty", "epic", TURN,
                     "Le temps s'écoule deux fois plus vite jusqu'à la fin du tour.")

    def start(self, ctx):
        ctx.set_time_scale(2.0)

    def stop(self, ctx):
        ctx.set_time_scale(1.0)


class TimeDilatation(Event):
    info = EventInfo("time_dilatation", "Dilatation du temps", "bonus", "rare", TURN,
                     "Le temps s'écoule deux fois moins vite jusqu'à la fin du tour.")

    def start(self, ctx):
        ctx.set_time_scale(0.5)

    def stop(self, ctx):
        ctx.set_time_scale(1.0)


class ColdRound(Event):
    info = EventInfo("cold_round", "Tour glacial", "penalty", "rare", 15,
                     "Indices gelés pendant 15 secondes. Les pénalités, elles, restent actives.")

    def start(self, ctx):
        ctx.set_hints_locked(True)

    def stop(self, ctx):
        ctx.set_hints_locked(False)


class TaxeEvent(Event):
    info = EventInfo("taxe_event", "L'impôt du roi", "penalty", "rare", UNTIL,
                     "Chaque erreur te coûte 5 points, jusqu'à ce que tu trouves 2 bonnes lettres.")

    def start(self, ctx):
        ctx.round.tax_per_miss = 5
        ctx.round.tax_hits_left = 2

    def stop(self, ctx):
        ctx.round.tax_per_miss = 0
        ctx.round.tax_hits_left = 0

    def finished(self, ctx):
        return ctx.round.tax_hits_left == 0


class GoldRun(Event):
    info = EventInfo("gold_run", "Ruée vers l'or", "bonus", "common", 15,
                     "Pendant 15 secondes, chaque lettre trouvée rapporte 5 points de plus.")

    def start(self, ctx):
        ctx.round.gold_per_tile = 5

    def stop(self, ctx):
        ctx.round.gold_per_tile = 0


class SecondChanceSave(Event):
    info = EventInfo("second_chance_save", "Seconde chance", "bonus", "rare", UNTIL,
                     "Ta prochaine erreur est annulée : tu gardes ta plume.")

    def start(self, ctx):
        ctx.round.shield = True

    def stop(self, ctx):
        ctx.round.shield = False

    def finished(self, ctx):
        return not ctx.round.shield


class DoubleOrNothing(Event):
    info = EventInfo("double_or_nothing", "Quitte ou double", "bonus", "epic", ROUND,
                     "Trouve ce mot : score doublé. Échoue : tu perds 20 points de ta bourse.")

    def start(self, ctx):
        ctx.round.double_or_nothing = True

    def stop(self, ctx):
        pass  # l'effet se règle à la fin du mot


ALL_EVENTS = {cls.info.key: cls for cls in (
    MirrorLetter, RandomScrambleFlask, LetterShuffle, HiddenTimer, TimePressure,
    TimeDilatation, ColdRound, TaxeEvent, GoldRun, SecondChanceSave, DoubleOrNothing,
)}


def roll_event(rng=random, kind=None) -> Event:
    """Tire un événement : d'abord bonus/pénalité, puis la rareté."""
    kind = kind or ("bonus" if rng.random() < BONUS_CHANCE else "penalty")
    r, acc, rarity = rng.random(), 0.0, "common"
    for name, weight in RARITY_WEIGHTS:
        acc += weight
        if r < acc:
            rarity = name
            break
    pool = [c for c in ALL_EVENTS.values() if c.info.kind == kind and c.info.rarity == rarity]
    pool = pool or [c for c in ALL_EVENTS.values() if c.info.kind == kind]
    return rng.choice(pool)()


# Moments du tour (fraction du temps restant) où un événement peut surgir
WINDOWS = {"early": (0.80, 0.90), "mid": (0.45, 0.60), "end": (0.15, 0.30)}


class EventDirector:
    """Planifie et fait vivre les événements. Un seul événement actif à la fois."""

    def __init__(self, level, rng=random, boss=False):
        self.level = level
        self.rng = rng
        self.boss = boss
        self.active = None
        self.left = 0.0
        self.turn = 0
        self.triggers = []

    @property
    def chance(self) -> float:
        return min(1.0, self.level.event_chance + (0.3 if self.boss else 0.0))

    def new_turn(self, turn_time: float) -> None:
        """Choisit les instants de déclenchement du tour. Pas d'événement au premier tour."""
        self.turn += 1
        windows = self.level.event_windows or (("mid",) if self.boss else ())
        self.triggers = [] if self.turn == 1 or not turn_time else sorted(
            (self.rng.uniform(*WINDOWS[w]) * turn_time for w in windows), reverse=True)

    def check(self, remaining: float):
        """Appelé à chaque frame avec le temps restant du tour. Renvoie un événement à lancer."""
        if not self.triggers or remaining > self.triggers[0]:
            return None
        self.triggers.pop(0)
        if self.active or self.rng.random() >= self.chance:
            return None
        return roll_event(self.rng)

    def begin(self, event, ctx) -> None:
        self.active = event
        duration = event.info.duration
        self.left = float(duration) if isinstance(duration, (int, float)) else 0.0
        event.start(ctx)

    def tick(self, dt: float, ctx) -> bool:
        """Fait avancer l'événement actif. Renvoie True s'il vient de se terminer."""
        ev = self.active
        if not ev:
            return False
        if isinstance(ev.info.duration, (int, float)):
            self.left -= dt
            if self.left <= 0:
                return self.end(ctx)
        elif ev.info.duration == UNTIL and ev.finished(ctx):
            return self.end(ctx)
        return False

    def end_turn(self, ctx) -> bool:
        if self.active and self.active.info.duration == TURN:
            return self.end(ctx)
        return False

    def end(self, ctx) -> bool:
        if not self.active:
            return False
        self.active.stop(ctx)
        self.active = None
        self.left = 0.0
        return True

    def progress(self) -> float:
        """Part de durée restante (1 = vient de commencer), pour la jauge."""
        ev = self.active
        if ev and isinstance(ev.info.duration, (int, float)):
            return max(0.0, self.left / ev.info.duration)
        return 1.0
