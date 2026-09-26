"""Règles du jeu, sans aucune dépendance à Kivy (testables avec unittest).

Round   : une manche = un mot à trouver.
Session : une partie complète dans un mode (un ou plusieurs mots).
"""
import random
from dataclasses import dataclass, field

from .config import (
    ANIME_CLUES, CHRONO_MISS_PENALTY, HARDCORE_TURN_TIME, LEVELS, MODES,
    WORD_GUESS_PENALTY,
)
from .words import fold

# Issues possibles d'une proposition
ALREADY, HIT, MISS, SHIELDED = "already", "hit", "miss", "shielded"


@dataclass
class GuessResult:
    kind: str
    positions: list = field(default_factory=list)
    lives_lost: int = 0
    won: bool = False
    lost: bool = False


class Round:
    """Un mot à deviner et tout l'état qui s'y rattache."""

    def __init__(self, entry, level, lives, unlimited_lives=False):
        self.entry = entry
        self.word = entry["word"]
        self.definition = entry.get("definition", "")
        self.theme = entry.get("theme", "")
        self.anime = entry.get("anime", "")   # mode Animé : titre de l'œuvre
        self.level = level
        self.max_lives = lives
        self.lives = lives
        self.unlimited_lives = unlimited_lives
        self.revealed = [False] * len(self.word)
        self.tried = set()          # lettres déjà proposées (sans accent)
        self.eliminated = set()     # clés retirées par l'indice « Éliminer 3 »
        self.errors = 0
        self.combo = 0
        self.best_combo = 0
        self.hints_used = []
        self.word_guess_bonus = 0
        self.guessed_whole_word_early = False
        # Effets posés par les événements
        self.shield = False         # second_chance_save : annule la prochaine erreur
        self.gold_per_tile = 0      # gold_run : points par lettre révélée
        self.gold_earned = 0
        self.double_or_nothing = False
        self.tax_per_miss = 0       # taxe_event
        self.tax_hits_left = 0
        self.tax_paid = 0

    # --- Lettres ------------------------------------------------------------
    @staticmethod
    def key(letter: str) -> str:
        """Une lettre et ses variantes accentuées partagent la même touche."""
        return fold(letter.lower())

    @property
    def word_keys(self) -> set:
        return {self.key(c) for c in self.word}

    def positions_of(self, letter: str) -> list:
        k = self.key(letter)
        return [i for i, c in enumerate(self.word) if self.key(c) == k]

    def hidden_count(self) -> int:
        return self.revealed.count(False)

    def key_state(self, letter: str) -> str:
        """État d'une touche du clavier : "", "hit" ou "miss"."""
        k = self.key(letter)
        if k in self.tried:
            return "hit" if k in self.word_keys else "miss"
        if k in self.eliminated:
            return "miss"
        return ""

    @property
    def won(self) -> bool:
        return all(self.revealed)

    @property
    def lost(self) -> bool:
        return not self.unlimited_lives and self.lives <= 0

    def reveal_start(self, ratio: float, rng=random) -> list:
        """Révèle quelques lettres au départ, sans jamais révéler tout le mot."""
        keys = sorted(self.word_keys)
        count = max(1, int(len(self.word) * ratio)) if ratio > 0 else 0
        count = min(count, len(keys) - 1)
        chosen = rng.sample(keys, count) if count > 0 else []
        positions = []
        for k in chosen:
            self.tried.add(k)
            for i, c in enumerate(self.word):
                if self.key(c) == k:
                    self.revealed[i] = True
                    positions.append(i)
        return sorted(positions)

    def _lose_lives(self, amount: int) -> int:
        if self.unlimited_lives:
            return 0
        lost = min(amount, self.lives)
        self.lives -= lost
        return lost

    def guess(self, letter: str) -> GuessResult:
        k = self.key(letter)
        if k in self.tried or k in self.eliminated:
            return GuessResult(ALREADY)
        self.tried.add(k)
        positions = [i for i, c in enumerate(self.word) if self.key(c) == k and not self.revealed[i]]
        if positions:
            for i in positions:
                self.revealed[i] = True
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.gold_earned += self.gold_per_tile * len(positions)
            if self.tax_hits_left:
                self.tax_hits_left -= 1
                if not self.tax_hits_left:
                    self.tax_per_miss = 0
            return GuessResult(HIT, positions, won=self.won)
        return self._miss(1)

    def _miss(self, amount: int) -> GuessResult:
        self.combo = 0
        if self.shield:
            self.shield = False
            return GuessResult(SHIELDED)
        self.errors += 1
        self.tax_paid += self.tax_per_miss
        lost = self._lose_lives(amount)
        return GuessResult(MISS, lives_lost=lost, lost=self.lost)

    def timeout(self) -> GuessResult:
        """Le temps du tour est écoulé : une plume perdue."""
        self.combo = 0
        lost = self._lose_lives(1)
        return GuessResult(MISS, lives_lost=lost, lost=self.lost)

    def guess_word(self, proposal: str) -> GuessResult:
        proposal = proposal.strip().lower()
        if not proposal:
            return GuessResult(ALREADY)
        if [self.key(c) for c in proposal] == [self.key(c) for c in self.word]:
            hidden = [i for i, r in enumerate(self.revealed) if not r]
            self.guessed_whole_word_early = len(hidden) * 2 >= len(self.word)
            self.word_guess_bonus = 10 * len(hidden)
            self.revealed = [True] * len(self.word)
            return GuessResult(HIT, hidden, won=True)
        return self._miss(WORD_GUESS_PENALTY)

    # --- Indices ------------------------------------------------------------
    def hint_letter(self, rng=random) -> list:
        hidden_keys = sorted({self.key(c) for c, r in zip(self.word, self.revealed) if not r})
        if len(hidden_keys) <= 1:
            return []  # ne jamais offrir la dernière lettre
        k = rng.choice(hidden_keys)
        self.tried.add(k)
        positions = [i for i, c in enumerate(self.word) if self.key(c) == k]
        for i in positions:
            self.revealed[i] = True
        self.hints_used.append("letter")
        return positions

    def hint_eliminate(self, count=3, rng=random) -> list:
        """Retire du clavier des lettres absentes du mot. Renvoie les touches concernées."""
        absent = sorted({
            self.key(c) for c in "abcdefghijklmnopqrstuvwxyz"
            if self.key(c) not in self.word_keys
            and self.key(c) not in self.tried and self.key(c) not in self.eliminated
        })
        chosen = rng.sample(absent, min(count, len(absent)))
        self.eliminated.update(chosen)
        if chosen:
            self.hints_used.append("eliminate")
        return chosen

    def note_hint(self, name: str):
        self.hints_used.append(name)

    # --- Score --------------------------------------------------------------
    def score_breakdown(self, extra=()) -> list:
        """Liste de (libellé, points). Vide si la manche est perdue."""
        if not self.won:
            return []
        lines = [(f"Mot {self.level.label}", self.level.base_score)]
        if not self.unlimited_lives:
            lines.append(("Plumes restantes x5", self.lives * 5))
        if self.best_combo >= 2:
            lines.append((f"Meilleur combo x{self.best_combo}", self.best_combo * 3))
        if self.word_guess_bonus:
            lines.append(("Mot entier deviné", self.word_guess_bonus))
        if self.gold_earned:
            lines.append(("Ruée vers l'or", self.gold_earned))
        lines.extend(extra)
        if self.double_or_nothing:
            lines.append(("Quitte ou double", sum(p for _, p in lines)))
        return lines

    def score(self, extra=()) -> int:
        return sum(p for _, p in self.score_breakdown(extra))

    @property
    def perfect(self) -> bool:
        return self.won and self.errors == 0 and not self.hints_used

    @property
    def clutch(self) -> bool:
        return self.won and not self.unlimited_lives and self.lives == 1


class Session:
    """Une partie dans un mode donné : choisit les mots, enchaîne les manches."""

    def __init__(self, mode_key, level_key, bank, recent=(), rng=random, today=None):
        self.mode = MODES[mode_key]
        self.chosen_level = self.mode.forced_level or level_key
        self.bank = bank
        self.recent = list(recent)
        self.rng = rng
        self.today = today
        self.rounds = []
        self.total_score = 0
        self.words_found = 0
        self.over = False
        self.time_left = float(self.mode.global_time)

    @property
    def index(self) -> int:
        return len(self.rounds)

    def level_for(self, index: int) -> str:
        if self.mode.key == "royal":
            return "noob" if index < 3 else "medium" if index < 7 else "hard"
        if self.mode.key == "chrono":
            return "noob" if index < 3 else "medium"
        return self.chosen_level

    def is_boss(self, index=None) -> bool:
        index = self.index - 1 if index is None else index
        return self.mode.key == "royal" and (index + 1) % 5 == 0

    def turn_time(self, level) -> int:
        if self.mode.no_turn_timer:
            return 0
        if self.mode.key == "hardcore":
            return HARDCORE_TURN_TIME
        return level.turn_time

    def next_round(self) -> Round:
        level = LEVELS[self.level_for(self.index)]
        if self.mode.key == "daily":
            entry = self.bank.daily(self.today)
        elif self.mode.key == "anime":
            entry = self.bank.pick_anime(self.recent, self.rng)
        else:
            entry = self.bank.pick(level.key, self.recent, self.rng)
        self.recent.append(entry["word"])
        lives = self.mode.lives
        if self.mode.key == "royal" and self.rounds:
            lives = min(self.mode.lives, self.rounds[-1].lives + 1)
        rnd = Round(entry, level, lives, unlimited_lives=bool(self.mode.global_time))
        self.rounds.append(rnd)
        return rnd

    def clues(self, rnd) -> list:
        """Mode Animé : indices gratuits selon la difficulté (libellé, texte)."""
        if self.mode.key != "anime":
            return []
        texts = {"anime": ("Animé", rnd.anime), "role": ("Rôle", rnd.theme), "description": ("", rnd.definition)}
        return [texts[k] for k in ANIME_CLUES[rnd.level.key]]

    def extra_score(self, rnd) -> list:
        extra = []
        if self.mode.key == "royal" and self.index > 1:
            extra.append((f"Série royale ({self.index} mots)", 5 * (self.index - 1)))
        if self.is_boss():
            extra.append(("Boss vaincu", 30))
        return extra

    def finish_round(self, rnd) -> int:
        """Clôt la manche en cours et décide si la partie continue."""
        points = rnd.score(self.extra_score(rnd))
        self.total_score += points
        if rnd.won:
            self.words_found += 1
        if self.mode.key == "chrono":
            self.over = self.time_left <= 0
        elif self.mode.chained:
            self.over = not rnd.won
        else:
            self.over = True
        return points

    def chrono_penalty(self, misses=1) -> None:
        self.time_left = max(0.0, self.time_left - CHRONO_MISS_PENALTY * misses)
