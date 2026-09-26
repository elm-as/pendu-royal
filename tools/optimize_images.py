"""Génère les images du jeu à partir des originaux haute résolution.

    python tools/optimize_images.py

Source : assets_src/images/png/  (1920 px, hors git)
Sortie : assets/images/png/      (rognées, redimensionnées, 256 couleurs)

Chaque image est rognée sur sa zone non transparente, réduite à la taille
maximale de son groupe puis quantifiée. Une image décodée occupe
largeur x hauteur x 4 octets en mémoire graphique : une plume de 1920x2552
coûtait ~20 Mo, elle en coûte maintenant ~0,2 Mo.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets_src" / "images" / "png"
DST = ROOT / "assets" / "images" / "png"

# nom source -> (nom de sortie, côté max en px)
FEATHERS = {f"f{i}": (f"f{i}", 160) for i in range(1, 10)}
EVENTS = {
    name: (name, 320)
    for name in (
        "cold_round", "double_or_nothing", "gold_run", "hidden_timer",
        "letter_shuffle", "mirror_letter", "random_scramble_flask",
        "second_chance_save", "taxe_event", "time_dilatation", "time_pressure",
    )
}
ACHIEVEMENTS = {
    name: (name, 320)
    for name in (
        "RG_1_m_1", "RG_1_m_2", "RG_1_m_3",
        "RG_2_m_1", "RG_2_m_2", "RG_2_m_3",
        "RG_3_m_1", "RG_3_m_2", "RG_3_m_3",
    )
}
MISC = {
    "IMG_20260218_125929": ("laurel", 640),
    "trophy": ("trophy", 320),
    "perfect": ("perfect", 256),
    "parameter": ("parameter", 192),
}
# Le pendu, la potence et l'icône sont générés par tools/make_hangman.py.
TARGETS = {**FEATHERS, **EVENTS, **ACHIEVEMENTS, **MISC}


def optimize(src: Path, dst: Path, max_side: int) -> None:
    im = Image.open(src).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        pad = max(4, (bbox[2] - bbox[0]) // 50)
        im = im.crop((
            max(0, bbox[0] - pad), max(0, bbox[1] - pad),
            min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad),
        ))
    im.thumbnail((max_side, max_side), Image.LANCZOS)
    im = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    im.save(dst, optimize=True)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Originaux introuvables : {SRC}")
    DST.mkdir(parents=True, exist_ok=True)
    before = after = 0
    for name, (out, side) in sorted(TARGETS.items()):
        src, dst = SRC / f"{name}.png", DST / f"{out}.png"
        optimize(src, dst, side)
        before += src.stat().st_size
        after += dst.stat().st_size
        print(f"{name:<22} -> {out:<18} {Image.open(dst).size}")
    print(f"\n{before / 1e6:.1f} Mo -> {after / 1e6:.2f} Mo")


if __name__ == "__main__":
    main()
