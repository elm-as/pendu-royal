"""Profil du joueur : chargement tolérant, migration, sauvegarde atomique."""
import copy
import json
import os
from datetime import date, timedelta
from pathlib import Path

from .config import LEVEL_ORDER, RECENT_WORDS_MEMORY, STARTING_POINTS

VERSION = 2

LEVEL_STATS = {
    "games": 0,
    "wins": 0,
    "defeats": 0,
    "streak": 0,
    "best_streak": 0,
    "perfect": 0,
    "clutch": 0,
    "hints_used": 0,
    "best_time": None,      # secondes, meilleure victoire
    "last_time": None,
    "best_score": 0,
    "total_score": 0,
    "last_played": "",
}

DEFAULT_PROFILE = {
    "version": VERSION,
    "points": STARTING_POINTS,
    "levels": {lvl: dict(LEVEL_STATS) for lvl in LEVEL_ORDER},  # une copie par niveau
    "modes": {
        "royal": {"games": 0, "best_words": 0, "best_score": 0},
        "chrono": {"games": 0, "best_words": 0, "best_score": 0},
        "hardcore": {"games": 0, "wins": 0, "best_score": 0},
        "daily": {"last_date": "", "streak": 0, "best_streak": 0, "played": 0, "wins": 0, "history": {}},
    },
    "totals": {
        "wins": 0, "perfect": 0, "perfect_streak": 0, "best_perfect_streak": 0,
        "points_earned": 0, "points_spent": 0,
    },
    "found_words": [],
    "recent_words": [],
    "achievements": {},
    "settings": {"sound": True, "vibration": True},
    "tutorial_done": False,
}


def _merge(defaults, data):
    """Complète `data` avec les valeurs par défaut manquantes (récursif)."""
    if not isinstance(defaults, dict) or not isinstance(data, dict):
        return copy.deepcopy(data)
    merged = copy.deepcopy(defaults)
    for key, value in data.items():
        merged[key] = _merge(defaults[key], value) if key in defaults else copy.deepcopy(value)
    return merged


def migrate_v1(old: dict) -> dict:
    """Convertit l'ancien format language/french/level/<niveau>[0]."""
    profile = copy.deepcopy(DEFAULT_PROFILE)
    levels = old.get("language", {}).get("french", {}).get("level", {})
    old_points = 0
    for lvl in LEVEL_ORDER:
        stats = levels.get(lvl)
        if isinstance(stats, list):  # ancien bug : tuple sérialisé en liste
            stats = stats[0] if stats else {}
        if not isinstance(stats, dict):
            continue
        new = profile["levels"][lvl]
        new["games"] = int(stats.get("games_played", 0))
        new["wins"] = int(stats.get("total_wins", 0))
        new["defeats"] = int(stats.get("total_defeates", 0))
        new["best_streak"] = int(stats.get("best_win_steak", 0))
        new["clutch"] = int(stats.get("clutch_wins", 0))
        profile["totals"]["wins"] += new["wins"]
        old_points += int(stats.get("points", 0))
    profile["points"] += old_points * 5
    profile["tutorial_done"] = profile["totals"]["wins"] > 0
    return profile


class Profile:
    def __init__(self, directory):
        self.path = Path(directory) / "user_account.json"
        self.data = self._load()

    def _load(self) -> dict:
        try:
            with open(self.path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except FileNotFoundError:
            return copy.deepcopy(DEFAULT_PROFILE)
        except (OSError, ValueError):
            # Fichier corrompu : on le met de côté au lieu de planter au démarrage.
            try:
                os.replace(self.path, self.path.with_suffix(".corrupt.json"))
            except OSError:
                pass
            return copy.deepcopy(DEFAULT_PROFILE)
        if not isinstance(raw, dict):
            return copy.deepcopy(DEFAULT_PROFILE)
        if "language" in raw and "version" not in raw:
            return migrate_v1(raw)
        return _merge(DEFAULT_PROFILE, raw)

    def save(self) -> None:
        """Écrit dans un fichier temporaire puis le renomme : jamais de JSON à moitié écrit."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=1)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)

    # --- Accès pratiques ----------------------------------------------------
    def __getitem__(self, key):
        return self.data[key]

    @property
    def settings(self) -> dict:
        return self.data["settings"]

    @property
    def points(self) -> int:
        return self.data["points"]

    def spend(self, amount: int) -> bool:
        if self.data["points"] < amount:
            return False
        self.data["points"] -= amount
        self.data["totals"]["points_spent"] += amount
        return True

    def earn(self, amount: int) -> None:
        amount = max(0, amount)
        self.data["points"] += amount
        self.data["totals"]["points_earned"] += amount

    def pay(self, amount: int) -> None:
        """Pénalité (taxe, quitte ou double) : le solde ne descend pas sous zéro."""
        self.data["points"] = max(0, self.data["points"] - amount)

    def level_stats(self, level: str) -> dict:
        return self.data["levels"][level]

    def remember_word(self, word: str) -> None:
        recent = self.data["recent_words"]
        if word in recent:
            recent.remove(word)
        recent.append(word)
        del recent[:-RECENT_WORDS_MEMORY]

    # --- Enregistrement des résultats ----------------------------------------
    def record_round(self, rnd, points: int, duration: float, count_level_stats: bool) -> None:
        self.remember_word(rnd.word)
        totals = self.data["totals"]
        if rnd.won:
            totals["wins"] += 1
            if rnd.word not in self.data["found_words"]:
                self.data["found_words"].append(rnd.word)
            if rnd.perfect:
                totals["perfect"] += 1
                totals["perfect_streak"] += 1
                totals["best_perfect_streak"] = max(totals["best_perfect_streak"], totals["perfect_streak"])
            else:
                totals["perfect_streak"] = 0
        else:
            totals["perfect_streak"] = 0
        self.earn(points)
        if not count_level_stats:
            return
        stats = self.level_stats(rnd.level.key)
        stats["games"] += 1
        stats["hints_used"] += len(rnd.hints_used)
        stats["last_played"] = date.today().isoformat()
        stats["last_time"] = round(duration, 1)
        if rnd.won:
            stats["wins"] += 1
            stats["streak"] += 1
            stats["best_streak"] = max(stats["best_streak"], stats["streak"])
            stats["perfect"] += rnd.perfect
            stats["clutch"] += rnd.clutch
            stats["total_score"] += points
            stats["best_score"] = max(stats["best_score"], points)
            if stats["best_time"] is None or duration < stats["best_time"]:
                stats["best_time"] = round(duration, 1)
        else:
            stats["defeats"] += 1
            stats["streak"] = 0

    def record_session(self, session) -> None:
        key = session.mode.key
        if key not in self.data["modes"]:
            return
        mode = self.data["modes"][key]
        if key == "daily":
            today = (session.today or date.today()).isoformat()
            yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
            won = session.words_found > 0
            mode["streak"] = (mode["streak"] + 1 if mode["last_date"] == yesterday else 1) if won else 0
            mode["best_streak"] = max(mode["best_streak"], mode["streak"])
            mode["last_date"] = today
            mode["played"] += 1
            mode["wins"] += won
            rnd = session.rounds[-1]
            mode["history"][today] = {"won": won, "errors": rnd.errors, "lives": rnd.lives, "max": rnd.max_lives}
            return
        mode["games"] += 1
        mode["best_score"] = max(mode["best_score"], session.total_score)
        if "best_words" in mode:
            mode["best_words"] = max(mode["best_words"], session.words_found)
        if "wins" in mode:
            mode["wins"] += session.words_found

    def daily_done(self, today: date = None) -> bool:
        today = (today or date.today()).isoformat()
        return self.data["modes"]["daily"]["last_date"] == today

    def reset_stats(self) -> None:
        keep = {"settings": self.data["settings"], "tutorial_done": True}
        self.data = copy.deepcopy(DEFAULT_PROFILE)
        self.data.update(keep)
