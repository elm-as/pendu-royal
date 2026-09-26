"""Compile et vérifie le dictionnaire.

    python tools/build_dictionary.py            # vérifie puis écrit assets/words/*.json
    python tools/build_dictionary.py --check    # vérifie seulement (code de sortie 1 si erreur)

Source : tools/words_src/{facile,corse,infernal}.txt, une ligne par mot :
    mot|Thème|Définition

Règles bloquantes : lettres françaises uniquement (a-z et accents),
4 à 12 lettres, pas de doublon entre niveaux, thème connu, définition présente.
Avertissements : la définition contient le mot (elle sert d'indice, le jeu le masque
mais mieux vaut l'éviter) ; mot absent de Lexique 3 ou non lemme, si
tools/Lexique383.tsv est présent (téléchargeable sur http://www.lexique.org).
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "words_src"
OUT = ROOT / "assets" / "words"
LEXIQUE = ROOT / "tools" / "Lexique383.tsv"

LEVELS = {"facile": "begin_words.json", "corse": "medium_words.json", "infernal": "hard_words.json"}
THEMES = {
    "Maison", "Objets", "Nature", "Animaux", "Corps & santé", "Émotions", "Caractère", "Société",
    "Travail", "Métiers", "Arts", "Sciences", "Histoire", "Lieux", "Cuisine", "Langue", "Temps",
    "Idées", "Actions", "Mystère",
}
# Mots absents de Lexique 3 (rares ou techniques) mais bien français, ou pluriels usuels.
WHITELIST = set("""
anaphore incipit zeugme yttrium exuvie tératologie halieutique amphibologie hémione vicariat
toxémie ballotine oxalique soufreux éboulure vacances ténèbres tréfonds zloty kobold yakitori
anicroche chevesne marigot épure
""".split())
LETTERS = re.compile(r"^[a-zàâäéèêëîïôöûüùç]+$")


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def parse(path: Path):
    entries = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            entries.append({"error": f"{path.name}:{n} format attendu mot|thème|définition"})
            continue
        entries.append({"word": parts[0], "theme": parts[1], "definition": parts[2], "where": f"{path.name}:{n}"})
    return entries


def load_lexique():
    if not LEXIQUE.exists():
        return None
    known, lemmas = set(), set()
    with open(LEXIQUE, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            known.add(row["ortho"])
            if row["islem"] == "1":
                lemmas.add(row["ortho"])
    return known, lemmas


ROLES = {"Protagoniste", "Méchant", "Allié", "Rival", "Mentor", "Anti-héros"}


def build_anime(errors: list) -> list:
    """Mode secret Animé : tools/words_src/anime.txt, une ligne nom|Animé|Rôle|Description."""
    result, seen = [], set()
    for n, line in enumerate((SRC / "anime.txt").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        where = f"anime.txt:{n}"
        if len(parts) != 4:
            errors.append(f"{where} format attendu nom|animé|rôle|description")
            continue
        name, anime, role, desc = parts
        if not LETTERS.match(name) or not 4 <= len(name) <= 12 or len(set(fold(name))) < 3:
            errors.append(f"{where} « {name} » : 4 à 12 lettres, sans espace ni tiret")
        if name in seen:
            errors.append(f"{where} « {name} » : en double")
        seen.add(name)
        if role not in ROLES:
            errors.append(f"{where} « {name} » : rôle inconnu « {role} »")
        if fold(name) in fold(anime.lower()).replace(" ", ""):
            errors.append(f"{where} « {name} » : le titre de l'animé donne la réponse")
        if fold(name) in fold(desc.lower()):
            errors.append(f"{where} « {name} » : la description contient le nom")
        result.append({"word": name, "anime": anime, "theme": role, "definition": desc})
    return result


def main(check_only: bool) -> int:
    errors, warnings = [], []
    lexique = load_lexique()
    seen = {}
    result = {}
    for level, out_name in LEVELS.items():
        entries = parse(SRC / f"{level}.txt")
        result[level] = []
        for e in entries:
            if "error" in e:
                errors.append(e["error"])
                continue
            w, where = e["word"], e["where"]
            if not LETTERS.match(w) or not fold(w).isascii():
                errors.append(f"{where} « {w} » : caractère non autorisé")
            if not 4 <= len(w) <= 12:
                errors.append(f"{where} « {w} » : doit faire 4 à 12 lettres (lisible sur téléphone)")
            if len(set(fold(w))) < 3:
                errors.append(f"{where} « {w} » : trop peu de lettres différentes")
            if w in seen:
                errors.append(f"{where} « {w} » : déjà présent ({seen[w]})")
            seen[w] = where
            if e["theme"] not in THEMES:
                errors.append(f"{where} « {w} » : thème inconnu « {e['theme']} »")
            if not e["definition"]:
                errors.append(f"{where} « {w} » : définition manquante")
            # le jeu masque les mots de la définition qui COMMENCENT par la racine du mot ;
            # on signale ceux qui la contiennent ailleurs (non masqués, donc l'indice trahit la réponse)
            stem = fold(w)[: max(4, len(w) - 3)]
            for token in re.findall(r"[\wÀ-ÿ]+", fold(e["definition"].lower())):
                if stem in token and not token.startswith(stem):
                    warnings.append(f"{where} « {w} » : la définition contient « {token} »")
            if lexique and w not in WHITELIST:
                known, lemmas = lexique
                if w not in known:
                    warnings.append(f"{where} « {w} » : absent de Lexique 3")
                elif w not in lemmas:
                    warnings.append(f"{where} « {w} » : pas un lemme (forme conjuguée ou plurielle ?)")
            result[level].append({"word": w, "definition": e["definition"], "theme": e["theme"]})

    anime = build_anime(errors)
    for msg in warnings:
        print("  attention :", msg)
    for msg in errors:
        print("  ERREUR :", msg)
    counts = ", ".join(f"{lvl} {len(v)}" for lvl, v in result.items())
    print(f"{sum(len(v) for v in result.values())} mots ({counts}) + {len(anime)} persos d'animé · {len(errors)} erreur(s) · {len(warnings)} avertissement(s)")
    if errors:
        return 1
    if not check_only:
        for level, out_name in LEVELS.items():
            data = sorted(result[level], key=lambda e: fold(e["word"]))
            (OUT / out_name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (OUT / "anime.json").write_text(json.dumps(anime, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Dictionnaire écrit dans", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
