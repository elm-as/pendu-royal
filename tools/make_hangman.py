"""Dessine le pendu royal, pièce par pièce (illustration vectorielle rendue avec Pillow).

    python tools/make_hangman.py

Produit dans assets/images/png/ :
    pendu_<pièce>.png           les pièces (9 étapes d'apparition, cf. LAYERS)
    pendu_face_calm/worry/dead   les expressions du roi
    pendu_hero.png               l'illustration complète (accueil, tutoriel)
    pendu_dead.png               version pendu (écran de défaite)
    icon.png                     icône de l'application
et assets/images/pendu_layout.json : position de chaque pièce dans le dessin
(chaque pièce est rognée pour ne pas gaspiller de mémoire graphique).

Toutes les coordonnées sont exprimées sur une toile de 1000 x 1000.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "images" / "png"
LAYOUT = ROOT / "assets" / "images" / "pendu_layout.json"

SS = 3                 # sur-échantillonnage (anticrénelage)
CANVAS = 1000
FINAL = 720            # taille de sortie de la toile complète
OUTLINE = "#24140A"
OW = 9                 # épaisseur du contour

WOOD = {"base": "#8A5530", "light": "#B97E48", "dark": "#5E361B", "grain": "#6B3F20"}
ROPE = {"base": "#D2AB70", "dark": "#8C6A3C", "light": "#EDD29C"}
KING = {
    "skin": "#F4CDA5", "skin_dark": "#DDA67B", "cheek": "#EE9C82",
    "robe": "#9B2335", "robe_dark": "#6E1424", "robe_light": "#C23A4C",
    "ermine": "#F6EEDC", "spot": "#2A1A12", "gold": "#E9AE3C", "gold_light": "#FFE08A",
    "gold_dark": "#A8741D", "gem_red": "#D0303F", "gem_blue": "#3E7DD6",
    "tights": "#3B2A4A", "shoe": "#2A1A12", "beard": "#E9E1D2",
}


def S(v):
    return int(round(v * SS))


def pts(points):
    return [(S(x), S(y)) for x, y in points]


class Layer:
    def __init__(self):
        self.im = Image.new("RGBA", (S(CANVAS), S(CANVAS)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def poly(self, points, fill, outline=OUTLINE, width=OW):
        self.d.polygon(pts(points), fill=fill, outline=outline, width=S(width) if outline else 0)

    def rrect(self, box, r, fill, outline=OUTLINE, width=OW):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle((S(x0), S(y0), S(x1), S(y1)), S(r), fill=fill,
                                 outline=outline, width=S(width) if outline else 0)

    def ellipse(self, box, fill, outline=OUTLINE, width=OW):
        x0, y0, x1, y1 = box
        self.d.ellipse((S(x0), S(y0), S(x1), S(y1)), fill=fill, outline=outline,
                       width=S(width) if outline else 0)

    def circle(self, cx, cy, r, fill, outline=OUTLINE, width=OW):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def line(self, points, fill, width, round_caps=True):
        p = pts(points)
        self.d.line(p, fill=fill, width=S(width), joint="curve")
        if round_caps:
            r = S(width) / 2
            for x, y in (p[0], p[-1]):
                self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def stroke(self, points, fill, width):
        """Trait épais avec contour sombre."""
        self.line(points, OUTLINE, width + 2 * OW)
        self.line(points, fill, width)


# ---------------------------------------------------------------- bois
def plank(layer, x0, y0, x1, y1, grains=2, vertical=False):
    layer.rrect((x0, y0, x1, y1), 10, WOOD["base"])
    # reflet et ombre
    if vertical:
        layer.rrect((x0 + 8, y0 + 8, x0 + (x1 - x0) * 0.38, y1 - 8), 6, WOOD["light"], outline=None)
        layer.rrect((x1 - (x1 - x0) * 0.22, y0 + 8, x1 - 8, y1 - 8), 6, WOOD["dark"], outline=None)
        for i in range(grains):
            gx = x0 + (x1 - x0) * (0.45 + 0.18 * i)
            layer.line([(gx, y0 + 30 + 40 * i), (gx + 4, (y0 + y1) / 2), (gx - 3, y1 - 40 - 30 * i)],
                       WOOD["grain"], 3)
    else:
        layer.rrect((x0 + 8, y0 + 8, x1 - 8, y0 + (y1 - y0) * 0.38), 6, WOOD["light"], outline=None)
        layer.rrect((x0 + 8, y1 - (y1 - y0) * 0.24, x1 - 8, y1 - 8), 6, WOOD["dark"], outline=None)
        for i in range(grains):
            gy = y0 + (y1 - y0) * (0.5 + 0.15 * i)
            layer.line([(x0 + 40 + 60 * i, gy), ((x0 + x1) / 2, gy + 3), (x1 - 50 - 40 * i, gy - 2)],
                       WOOD["grain"], 3)
    # redessine le contour par-dessus les reflets
    layer.d.rounded_rectangle((S(x0), S(y0), S(x1), S(y1)), S(10), outline=OUTLINE, width=S(OW))


def bolt(layer, x, y):
    layer.circle(x, y, 9, "#6D6A66", width=5)
    layer.circle(x - 2, y - 2, 3, "#B8B4AE", outline=None)


def rotated_plank(layer, p0, p1, thickness):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * thickness / 2, dx / length * thickness / 2
    corners = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
    layer.poly(corners, WOOD["base"])
    hl = [(x0 + nx * 0.8, y0 + ny * 0.8), (x1 + nx * 0.8, y1 + ny * 0.8),
          (x1 + nx * 0.15, y1 + ny * 0.15), (x0 + nx * 0.15, y0 + ny * 0.15)]
    layer.poly(hl, WOOD["light"], outline=None)
    layer.line([(x0 - nx * 0.35 + dx * 0.1, y0 - ny * 0.35 + dy * 0.1),
                (x1 - nx * 0.35 - dx * 0.1, y1 - ny * 0.35 - dy * 0.1)], WOOD["grain"], 3)
    layer.d.polygon(pts(corners), outline=OUTLINE, width=S(OW))


# ---------------------------------------------------------------- corde
def rope_segment(layer, x, y0, y1, width=16):
    layer.stroke([(x, y0), (x, y1)], ROPE["base"], width)
    y = y0 + 6
    while y < y1 - 6:  # torsades
        layer.line([(x - width / 2 + 2, y + 7), (x + width / 2 - 2, y - 4)], ROPE["dark"], 3, round_caps=False)
        y += 13
    layer.line([(x - width / 4, y0 + 4), (x - width / 4, y1 - 4)], ROPE["light"], 2, round_caps=False)


# ---------------------------------------------------------------- pièces
X_ROPE, NECK_Y = 640, 492
HEAD_CX, HEAD_CY, HEAD_R = 640, 408, 74


def piece_base(L):
    L.ellipse((70, 905, 760, 965), (0, 0, 0, 70), outline=None)          # ombre au sol
    plank(L, 60, 862, 720, 930, grains=2)
    for x in (130, 330, 560):
        bolt(L, x, 896)


def piece_pole(L):
    plank(L, 158, 100, 232, 880, grains=2, vertical=True)
    bolt(L, 195, 820)


def piece_beam(L):
    plank(L, 120, 82, 730, 148, grains=2)
    bolt(L, 195, 115)
    L.rrect((620, 144, 660, 168), 6, "#6D6A66", width=5)                  # crochet de la corde


def piece_brace(L):
    rotated_plank(L, (205, 360), (400, 140), 44)
    bolt(L, 222, 340)
    bolt(L, 382, 158)


def piece_rope(L):
    """Corde et nœud coulant (derrière la tête)."""
    rope_segment(L, X_ROPE, 160, 380)
    for i in range(5):  # spires du nœud, visibles au-dessus de la couronne avant l'arrivée du roi
        y = 250 + i * 16
        L.rrect((X_ROPE - 17, y, X_ROPE + 17, y + 18), 8, ROPE["base"], width=6)
        L.line([(X_ROPE - 10, y + 13), (X_ROPE + 10, y + 5)], ROPE["dark"], 3, round_caps=False)
    rope_segment(L, X_ROPE, 330, NECK_Y + 10, width=14)


def piece_noose(L):
    """Boucle autour du cou, dessinée devant le col du roi."""
    box = (X_ROPE - 46, NECK_Y + 8, X_ROPE + 46, NECK_Y + 40)
    L.ellipse(box, None, outline=OUTLINE, width=26)
    L.ellipse(box, None, outline=ROPE["base"], width=13)
    for dx in (-30, -10, 10, 30):
        L.line([(X_ROPE + dx - 4, NECK_Y + 36), (X_ROPE + dx + 4, NECK_Y + 30)], ROPE["dark"], 3, round_caps=False)
    L.circle(X_ROPE + 42, NECK_Y + 22, 13, ROPE["base"], width=6)


def piece_head(L):
    cx, cy, r = HEAD_CX, HEAD_CY, HEAD_R
    # oreilles
    for sx in (-1, 1):
        L.circle(cx + sx * (r - 4), cy + 8, 17, KING["skin_dark"])
    L.circle(cx, cy, r, KING["skin"])
    # barbe royale
    beard = [(cx - r + 10, cy + 10), (cx - r + 22, cy + 52), (cx - 30, cy + r + 18), (cx, cy + r + 30),
             (cx + 30, cy + r + 18), (cx + r - 22, cy + 52), (cx + r - 10, cy + 10),
             (cx + 36, cy + 34), (cx, cy + 42), (cx - 36, cy + 34)]
    L.poly(beard, KING["beard"])
    # moustache
    L.ellipse((cx - 40, cy + 22, cx - 2, cy + 42), KING["beard"], width=6)
    L.ellipse((cx + 2, cy + 22, cx + 40, cy + 42), KING["beard"], width=6)
    # nez
    L.ellipse((cx - 13, cy + 2, cx + 13, cy + 28), KING["skin_dark"], width=6)
    # couronne
    base_y = cy - r + 14
    crown = [(cx - 66, base_y + 10), (cx - 74, base_y - 64), (cx - 38, base_y - 28), (cx, base_y - 82),
             (cx + 38, base_y - 28), (cx + 74, base_y - 64), (cx + 66, base_y + 10)]
    L.poly(crown, KING["gold"])
    L.poly([(cx - 58, base_y - 4), (cx - 64, base_y - 44), (cx - 36, base_y - 16), (cx - 36, base_y - 4)],
           KING["gold_light"], outline=None)
    L.rrect((cx - 70, base_y - 8, cx + 70, base_y + 18), 8, KING["gold_dark"])
    for gx, col in ((cx - 40, KING["gem_blue"]), (cx, KING["gem_red"]), (cx + 40, KING["gem_blue"])):
        L.circle(gx, base_y + 5, 8, col, width=4)
    for tx, ty in ((cx - 74, base_y - 64), (cx, base_y - 82), (cx + 74, base_y - 64)):
        L.circle(tx, ty, 10, KING["gold_light"], width=5)


def face(kind):
    L = Layer()
    cx, cy = HEAD_CX, HEAD_CY
    if kind == "dead":
        for ex in (cx - 28, cx + 28):
            L.line([(ex - 13, cy - 25), (ex + 13, cy - 3)], OUTLINE, 8)
            L.line([(ex - 13, cy - 3), (ex + 13, cy - 25)], OUTLINE, 8)
        L.ellipse((cx - 14, cy + 44, cx + 14, cy + 60), OUTLINE, outline=None)  # bouche ouverte
        L.line([(cx + 4, cy + 56), (cx + 12, cy + 74)], "#E0707A", 9)            # langue
    else:
        worried = kind == "worry"
        for ex in (cx - 28, cx + 28):
            L.ellipse((ex - 13, cy - 30, ex + 13, cy + 0), "white", width=5)
            L.circle(ex + (0 if worried else 2), cy - 13 + (3 if worried else 0), 7, OUTLINE, outline=None)
            L.circle(ex + 2, cy - 17, 2.5, "white", outline=None)
        # sourcils
        tilt = 12 if worried else -4
        L.line([(cx - 44, cy - 38 + (0 if worried else 4)), (cx - 14, cy - 38 - tilt)], OUTLINE, 6)
        L.line([(cx + 14, cy - 38 - tilt), (cx + 44, cy - 38 + (0 if worried else 4))], OUTLINE, 6)
        if worried:
            L.ellipse((cx - 10, cy + 44, cx + 10, cy + 62), OUTLINE, outline=None)
            L.ellipse((cx + 50, cy - 50, cx + 64, cy - 28), "#8FD3F5", width=4)  # goutte de sueur
        else:
            L.d.arc((S(cx - 16), S(cy + 40), S(cx + 16), S(cy + 60)), 20, 160, fill=OUTLINE, width=S(6))
        for sx in (-1, 1):
            L.ellipse((cx + sx * 46 - 12, cy + 4, cx + sx * 46 + 12, cy + 18), KING["cheek"] + "90", outline=None)
    return L


def piece_body(L):
    cx, top, bottom = HEAD_CX, NECK_Y + 6, 720
    robe = [(cx - 42, top), (cx + 42, top), (cx + 92, bottom), (cx - 92, bottom)]
    L.poly(robe, KING["robe"])
    L.poly([(cx - 36, top + 6), (cx - 6, top + 6), (cx - 30, bottom - 4), (cx - 84, bottom - 4)],
           KING["robe_light"], outline=None)
    L.poly([(cx + 20, top + 6), (cx + 38, top + 6), (cx + 86, bottom - 4), (cx + 52, bottom - 4)],
           KING["robe_dark"], outline=None)
    L.d.polygon(pts(robe), outline=OUTLINE, width=S(OW))
    # bordure d'hermine
    L.rrect((cx - 100, bottom - 26, cx + 100, bottom + 8), 14, KING["ermine"])
    for sx in (-70, -30, 10, 50, 85):
        L.poly([(cx + sx, bottom - 16), (cx + sx - 5, bottom - 2), (cx + sx + 5, bottom - 2)], KING["spot"], outline=None)
    # col d'hermine
    L.ellipse((cx - 66, top - 16, cx + 66, top + 38), KING["ermine"])
    for sx in (-40, 0, 40):
        L.poly([(cx + sx, top + 6), (cx + sx - 5, top + 20), (cx + sx + 5, top + 20)], KING["spot"], outline=None)
    # ceinture et boucle
    L.poly([(cx - 64, 612), (cx + 64, 612), (cx + 68, 638), (cx - 68, 638)], KING["gold_dark"])
    L.rrect((cx - 16, 606, cx + 16, 644), 6, KING["gold"], width=6)


def piece_arms(L):
    cx = HEAD_CX
    for sx in (-1, 1):
        shoulder, hand = (cx + sx * 50, NECK_Y + 34), (cx + sx * 104, 660)
        L.stroke([shoulder, (cx + sx * 88, 580), hand], KING["robe"], 34)
        L.line([(cx + sx * 56, NECK_Y + 44), (cx + sx * 84, 584)], KING["robe_light"], 8)
        L.rrect((hand[0] - 26, hand[1] - 12, hand[0] + 26, hand[1] + 8), 8, KING["ermine"], width=6)  # manchette
        L.circle(hand[0], hand[1] + 26, 20, KING["skin"])


def piece_legs(L):
    cx = HEAD_CX
    for sx in (-1, 1):
        L.stroke([(cx + sx * 30, 728), (cx + sx * 36, 830)], KING["tights"], 30)
        shoe = [(cx + sx * 20, 824), (cx + sx * 52, 824), (cx + sx * 78, 842), (cx + sx * 50, 852), (cx + sx * 20, 850)]
        L.poly(shoe, KING["shoe"])


# (nom, fonction, étape d'apparition 1..9), dans l'ordre de superposition (du fond vers l'avant)
LAYERS = (
    ("pendu_base", piece_base, 1),
    ("pendu_pole", piece_pole, 2),
    ("pendu_brace", piece_brace, 4),
    ("pendu_beam", piece_beam, 3),
    ("pendu_rope", piece_rope, 5),
    ("pendu_legs", piece_legs, 9),
    ("pendu_body", piece_body, 7),
    ("pendu_arms", piece_arms, 8),
    ("pendu_head", piece_head, 6),
    ("pendu_noose", piece_noose, 5),
)


def finish(layer: Layer, size: int) -> Image.Image:
    return layer.im.resize((size, size), Image.LANCZOS)


def save_cropped(im: Image.Image, name: str, layout: dict):
    bbox = im.getchannel("A").getbbox()
    crop = im.crop(bbox)
    crop.save(OUT / f"{name}.png", optimize=True)
    w, h = im.size
    # boîte normalisée, origine en bas à gauche (repère Kivy)
    layout[name] = [bbox[0] / w, 1 - bbox[3] / h, (bbox[2] - bbox[0]) / w, (bbox[3] - bbox[1]) / h]


def composite(face_kind: str) -> Image.Image:
    full = Image.new("RGBA", (S(CANVAS), S(CANVAS)), (0, 0, 0, 0))
    for name, fn, _stage in LAYERS:
        L = Layer()
        fn(L)
        full.alpha_composite(L.im)
        if name == "pendu_head":
            full.alpha_composite(face(face_kind).im)
    return full


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("pendu_*.png"):
        old.unlink()
    boxes = {}
    for name, fn, _stage in LAYERS:
        L = Layer()
        fn(L)
        save_cropped(finish(L, FINAL), name, boxes)
    for kind in ("calm", "worry", "dead"):
        save_cropped(finish(face(kind), FINAL), f"pendu_face_{kind}", boxes)
    layout = {
        "layers": [{"name": n, "stage": st, "box": boxes[n]} for n, _f, st in LAYERS],
        "faces": {k: boxes[f"pendu_face_{k}"] for k in ("calm", "worry", "dead")},
        "face_after": "pendu_head",
    }
    hero = composite("worry").resize((FINAL, FINAL), Image.LANCZOS)
    hb = hero.getchannel("A").getbbox()
    hero.crop(hb).save(OUT / "pendu_hero.png", optimize=True)
    # zone de la couronne dans pendu_hero.png (normalisée, origine en bas à gauche) : le secret de l'accueil
    k = FINAL / CANVAS
    top = HEAD_CY - HEAD_R + 14
    x0, y0, x1, y1 = [v * k for v in (HEAD_CX - 90, top - 100, HEAD_CX + 90, top + 24)]
    w, h = hb[2] - hb[0], hb[3] - hb[1]
    layout["hero_crown"] = [(x0 - hb[0]) / w, 1 - (y1 - hb[1]) / h, (x1 - x0) / w, (y1 - y0) / h]
    LAYOUT.write_text(json.dumps(layout, indent=1), encoding="utf-8")
    dead = composite("dead").resize((FINAL, FINAL), Image.LANCZOS)
    dead.crop(dead.getchannel("A").getbbox()).save(OUT / "pendu_dead.png", optimize=True)

    # icône : la tête couronnée sur un médaillon doré
    icon = Image.new("RGBA", (S(CANVAS), S(CANVAS)), (0, 0, 0, 0))
    medal = Layer()
    medal.circle(500, 500, 470, "#3A2619", outline="#E9AE3C", width=40)
    icon.alpha_composite(medal.im)
    head = Layer()
    piece_head(head)
    head.im.alpha_composite(face("worry").im)
    head_im = head.im.crop((S(HEAD_CX - 130), S(HEAD_CY - 180), S(HEAD_CX + 130), S(HEAD_CY + 130)))
    head_im = head_im.resize((S(620), S(int(620 * 310 / 260))), Image.LANCZOS)
    icon.alpha_composite(head_im, (S(190), S(150)))
    icon.resize((512, 512), Image.LANCZOS).save(OUT / "icon.png", optimize=True)
    print("Pendu généré :", ", ".join(n for n, _f, _s in LAYERS))


if __name__ == "__main__":
    main()
