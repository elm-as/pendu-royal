"""Dictionnaire : chargement unique, tirage sans répétition, mot du jour."""
import hashlib
import json
import random
import re
import unicodedata
from datetime import date

from .config import ASSETS, LEVEL_ORDER

WORD_FILES = {"noob": "begin_words.json", "medium": "medium_words.json", "hard": "hard_words.json"}


def fold(text: str) -> str:
    """Retire les accents : « é » -> « e », « ç » -> « c »."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def mask_definition(definition: str, word: str) -> str:
    """Cache le mot et ses dérivés dans la définition (utilisée comme indice)."""
    root = fold(word.lower())
    stem = root[: max(4, len(root) - 3)]

    def hide(match):
        token = match.group(0)
        return "____" if fold(token.lower()).startswith(stem) else token

    return re.sub(r"[\wÀ-ÿ]+", hide, definition)


class WordBank:
    def __init__(self, directory=ASSETS / "words"):
        self.words = {}
        for level, name in WORD_FILES.items():
            with open(directory / name, encoding="utf-8") as fh:
                self.words[level] = json.load(fh)

    def pick(self, level: str, recent=(), rng=random) -> dict:
        """Tire un mot du niveau en évitant les mots joués récemment."""
        entries = self.words[level]
        recent = set(recent)
        fresh = [e for e in entries if e["word"] not in recent]
        return rng.choice(fresh or entries)

    def daily(self, day: date = None) -> dict:
        """Mot du jour : identique sur tous les appareils pour une même date."""
        day = day or date.today()
        entries = self.words["medium"]
        digest = hashlib.sha256(f"pendu-royal-{day.isoformat()}".encode()).hexdigest()
        return entries[int(digest, 16) % len(entries)]

    def count(self) -> int:
        return sum(len(self.words[lvl]) for lvl in LEVEL_ORDER)
