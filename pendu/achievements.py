"""Succès : chacun correspond à une médaille dessinée (assets/images/png/RG_*)."""
from dataclasses import dataclass
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class Achievement:
    key: str
    title: str
    description: str
    image: str
    check: Callable  # (profile_data, session) -> bool


def _modes(p, key):
    return p["modes"][key]


ACHIEVEMENTS = (
    Achievement("conquerant", "Conquérant des mots", "Remporter 50 manches, tous modes confondus.",
                "RG_1_m_1", lambda p, s: p["totals"]["wins"] >= 50),
    Achievement("maitre", "Maître du lexique", "Trouver 150 mots différents.",
                "RG_1_m_2", lambda p, s: len(p["found_words"]) >= 150),
    Achievement("immortel", "Immortel des lettres", "10 victoires parfaites (sans erreur ni indice).",
                "RG_1_m_3", lambda p, s: p["totals"]["perfect"] >= 10),
    Achievement("gardien", "Maître de l'Infernal", "Gagner 25 parties classiques en Infernal.",
                "RG_2_m_1", lambda p, s: p["levels"]["hard"]["wins"] >= 25),
    Achievement("instinct", "Instinct infaillible", "Enchaîner 5 victoires parfaites.",
                "RG_2_m_2", lambda p, s: p["totals"]["best_perfect_streak"] >= 5),
    Achievement("prophete", "Prophète du verbe", "Deviner le mot entier alors que la moitié des lettres sont cachées.",
                "RG_2_m_3", lambda p, s: s is not None and any(r.guessed_whole_word_early for r in s.rounds)),
    Achievement("miracule", "Miraculé du pendu", "Gagner avec une seule plume restante.",
                "RG_3_m_1", lambda p, s: s is not None and any(r.clutch for r in s.rounds)),
    Achievement("chat", "Chat à neuf lettres", "Survivre à 9 mots d'affilée en Mode Royal.",
                "RG_3_m_2", lambda p, s: _modes(p, "royal")["best_words"] >= 9),
    Achievement("indestructible", "L'indestructible", "Gagner une partie Sans filet.",
                "RG_3_m_3", lambda p, s: _modes(p, "hardcore")["wins"] >= 1),
)


def unlock_new(profile_data: dict, session=None) -> list:
    """Débloque les succès nouvellement obtenus et les renvoie."""
    unlocked = profile_data["achievements"]
    new = []
    for ach in ACHIEVEMENTS:
        if ach.key not in unlocked and ach.check(profile_data, session):
            unlocked[ach.key] = date.today().isoformat()
            new.append(ach)
    return new
