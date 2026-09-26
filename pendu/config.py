"""Constantes du jeu : chemins, palette, niveaux, modes, coûts."""
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def img(name: str) -> str:
    """Chemin absolu d'une image (indépendant du dossier de lancement)."""
    return str(ASSETS / "images" / "png" / f"{name}.png")


def font(name: str) -> str:
    return str(ASSETS / "fonts" / f"{name}.ttf")


def sound(name: str) -> str:
    return str(ASSETS / "sounds" / f"{name}.wav")


# Palette « bois sombre, parchemin et or ». Toutes les couleurs de l'interface
# passent par ce dictionnaire.
COLORS = {
    "bg_top": "#2B1B12",
    "bg_bottom": "#120B07",
    "panel": "#3A2619",
    "panel_light": "#4E3322",
    "border": "#6B4527",
    "parchment": "#F3E3C3",
    "parchment_dark": "#DCC398",
    "ink": "#3B2414",
    "text": "#F7EBD3",
    "muted": "#BFA78A",
    "gold": "#E5A83B",
    "gold_dark": "#A8741D",
    "brand": "#DC7913",
    "hit": "#4E9F5A",
    "hit_dark": "#2F6B3A",
    "miss": "#5A4A40",
    "danger": "#C0392B",
    "bonus": "#3FA7D6",
    "penalty": "#B04ACF",
    "wood": "#7A4B2A",
    "rope": "#C9A26B",
}

# Clavier AZERTY sans accents : « e » révèle aussi é, è, ê, ë ; « c » révèle ç.
KEYBOARD_ROWS = (
    "azertyuiop",
    "qsdfghjklm",
    "wxcvbn",
)
KEYBOARD_LETTERS = frozenset("".join(KEYBOARD_ROWS))


@dataclass(frozen=True)
class Level:
    key: str
    label: str
    color: str
    turn_time: int          # secondes par tour (un tour = jusqu'à la prochaine lettre validée)
    reveal_ratio: float     # part des lettres révélées au départ
    event_windows: tuple    # moments du tour où un événement peut apparaître
    event_chance: float     # probabilité d'événement à chaque fenêtre
    base_score: int


LEVELS = {
    "noob": Level("noob", "Facile", "#6CC070", 40, 0.30, (), 0.0, 10),
    "medium": Level("medium", "Corsé", "#F1C40F", 35, 0.20, ("end",), 0.40, 20),
    "hard": Level("hard", "Infernal", "#B06BD6", 30, 0.10, ("early", "mid", "end"), 0.50, 40),
}
LEVEL_ORDER = ("noob", "medium", "hard")


@dataclass(frozen=True)
class Mode:
    key: str
    label: str
    tagline: str
    lives: int = 9
    hints: bool = True
    chained: bool = False         # enchaîne les mots dans une même partie
    global_time: int = 0          # > 0 : chrono global en secondes (contre-la-montre)
    no_turn_timer: bool = False
    forced_level: str = ""        # niveau imposé (sinon choisi par le joueur)
    reveal_letters: bool = True


MODES = {
    "classic": Mode("classic", "Classique", "Un mot, neuf plumes. Choisis ta difficulté."),
    "royal": Mode(
        "royal", "Mode Royal",
        "Survie : les mots s'enchaînent et durcissent. +1 plume par mot trouvé. Un boss tous les 5 mots.",
        chained=True,
    ),
    "chrono": Mode(
        "chrono", "Contre-la-montre",
        "3 minutes pour trouver un maximum de mots. Une erreur coûte 5 secondes.",
        lives=6, chained=True, global_time=180, no_turn_timer=True,
    ),
    "hardcore": Mode(
        "hardcore", "Sans filet",
        "Infernal, 3 plumes, aucune lettre offerte, aucun indice. Pour les vrais.",
        lives=3, hints=False, forced_level="hard", reveal_letters=False,
    ),
    "daily": Mode(
        "daily", "Défi du jour",
        "Le même mot pour tout le monde, un seul essai par jour.",
        forced_level="medium",
    ),
}

HINTS = {
    "letter": ("Lettre", 15),
    "eliminate": ("Éliminer 3", 10),
    "theme": ("Thème", 8),
    "definition": ("Définition", 25),
}

WORD_GUESS_PENALTY = 2   # plumes perdues pour une mauvaise proposition de mot entier
CHRONO_MISS_PENALTY = 5  # secondes perdues par erreur en contre-la-montre
HARDCORE_TURN_TIME = 20
STARTING_POINTS = 50
RECENT_WORDS_MEMORY = 60
