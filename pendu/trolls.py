"""Les petites surprises cachées pour Manassé.

Le roi le connaît : il le salue au lancement et commente ses parties.
Faux bug : de temps en temps, un faux plantage… qui n'en est pas un.
"""
import random

NAME = "Manassé"

GREETINGS = (
    f"Salut {NAME} ! Prêt à perdre ?",
    f"Oh non… encore toi, {NAME}.",
    f"Le roi t'attendait, {NAME}.",
    f"{NAME} est de retour. Cachez les cordes.",
    f"Bonjour {NAME}. Le bourreau a pris son café.",
    f"Tiens, {NAME} ! On révise son alphabet aujourd'hui ?",
)

DEFEAT = (
    f"Même mon chat aurait trouvé, {NAME}.",
    f"{NAME}, le dictionnaire porte plainte.",
    f"Je suis pendu à cause de toi, {NAME}. Encore.",
    f"On en reparlera au tribunal, {NAME}.",
    f"{NAME}… tu l'as fait exprès, avoue.",
    f"Ma couronne a honte pour toi, {NAME}.",
    f"Respire, {NAME}. C'est juste un mot. Un tout petit mot.",
)

VICTORY = (
    f"Pas mal, {NAME}. Pour une fois.",
    f"Le roi te doit la vie, {NAME}. Ne le répète à personne.",
    f"Coup de chance, {NAME}. J'en suis sûr.",
    f"Bien joué, {NAME}. Le bourreau est déçu.",
    f"Tu m'as sauvé, {NAME}. Je retire (presque) tout.",
)

PERFECT = (
    f"Sans une seule erreur ?! Qui es-tu et qu'as-tu fait de {NAME} ?",
    f"Parfait. Le roi s'incline devant {NAME}.",
)

MISS_STREAK = (
    f"{NAME}… vraiment ?",
    f"Le roi commence à transpirer, {NAME}.",
    f"Trois ratés d'affilée, {NAME}. Tu me veux mort ?",
)

FAKE_CRASH_CHANCE = 0.06   # par erreur commise
FAKE_CRASH_MIN_GAMES = 2   # jamais pendant les toutes premières parties


def pick(lines, rng=random) -> str:
    return rng.choice(lines)


def result_quote(won: bool, perfect: bool, rng=random) -> str:
    if won and perfect:
        return pick(PERFECT, rng)
    return pick(VICTORY if won else DEFEAT, rng)
