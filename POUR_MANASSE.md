# Pour Manassé 👑

Salut Manassé,

J'ai passé du temps sur ton **Pendu Royal**, et avant de te parler de ce que j'ai modifié, je veux te dire un truc clairement : **ton projet avait déjà une vraie âme.** Tout ce que j'ai fait, je l'ai construit *sur* tes idées. Sans elles, il n'y aurait rien eu à améliorer.

Voici un bilan honnête : ce qui était déjà top, les erreurs que j'ai trouvées (et ce qu'elles t'apprennent), et ce qui a changé.

---

## 1. Ce que tu as fait de très bien

**Ton concept est original.** Un pendu, tout le monde connaît. Mais les **plumes comme points de vie** et les **événements aléatoires** en pleine partie, c'est une vraie idée de game design. C'est exactement ce qui transforme un jeu classique en *ton* jeu.

**Tes 11 événements sont excellents.** Lettres inversées, lettres mélangées, clavier qui change de disposition, timer invisible, temps qui accélère ou ralentit, quitte ou double, seconde chance… Tu les avais pensés avec un type (bonus ou pénalité), une rareté (commun, rare, épique) et une description, et 6 d'entre eux fonctionnaient déjà. C'est une démarche de vrai concepteur de jeu. Je les ai tous gardés, je leur ai donné un nom affiché en jeu (« Lettres miroir », « Fiole du chaos »…), et j'ai codé les 5 qui n'avaient encore que leur description.

**Tes illustrations sont superbes.** Les 9 plumes, les 11 badges d'événements, et surtout les **9 médailles de succès** (« Conquérant des mots », « Miraculé du pendu », « Chat à neuf lettres »…). Elles n'étaient même pas encore utilisées dans le jeu : maintenant, ce sont les vrais succès à débloquer.

**Tu avais déjà le souci du détail.** Les lettres qui apparaissent une par une à la fin, la définition qui s'écrit comme à la machine, les couleurs qui changent quand on appuie sur un bouton… Tu pensais à ce que ressent le joueur. C'est la qualité la plus importante pour faire des jeux, et beaucoup de développeurs ne l'ont pas.

**Tu étais organisé.** Toutes tes couleurs rangées dans un seul dictionnaire (`COLORS_PALETTE`), les événements chacun dans leur fichier (`events/`), des docstrings pour expliquer tes méthodes. C'est la bonne direction.

**Et tu as fini quelque chose de jouable**, avec 1 400 lignes de Python, 2 000 lignes de Kivy, trois niveaux, des stats et 578 mots avec leur définition. Aller au bout d'un projet de cette taille, c'est déjà beaucoup.

---

## 2. Les erreurs que j'ai trouvées (et ce qu'elles t'apprennent)

Aucune de ces erreurs n'est « bête ». Ce sont les **erreurs classiques** que tout le monde fait en apprenant, moi compris. Le mieux, c'est de comprendre *pourquoi* elles arrivent.

### 🐛 La virgule fantôme

```python
self.default_user_stat = {
    "games_played": 0,
    ...
},          # ← cette virgule
```

Cette petite virgule transforme ton dictionnaire en **tuple** (une liste qui contient ton dictionnaire). C'est pour ça que tu devais écrire `[0]` partout (`...["noob"][0]["games_played"]`). Ton commentaire disait que « le module json le modifie en liste », mais le coupable, c'était la virgule !

> **Leçon :** quand un comportement te paraît bizarre, affiche le type (`print(type(x))`). Ça règle souvent le mystère en une seconde.

### 🐛 Les trois niveaux qui partageaient les mêmes stats

```python
"noob": self.default_user_stat,
"medium": self.default_user_stat,
"hard": self.default_user_stat,
```

En Python, ça ne crée pas trois copies : les trois clés pointent vers **le même objet**. Une victoire en Facile modifiait donc aussi les stats de Corsé et d'Infernal (au moins jusqu'au redémarrage de l'appli).

> **Leçon :** en Python, `a = b` ne copie pas, ça donne un deuxième nom à la même chose. Pour copier, il faut `dict(b)` ou `copy.deepcopy(b)`.

### 🐛 Le niveau toujours « Infernal »

```python
def get_level(self):
    if self.ids.level_name == "Facile":   # on compare un Label à un texte
```

`self.ids.level_name` est un **widget**, pas un texte : la comparaison était toujours fausse, et la fonction renvoyait toujours `"hard"`. Résultat : les événements apparaissaient même en Facile. Il fallait écrire `self.ids.level_name.text == "Facile"`.

> **Leçon :** fais attention à la différence entre un objet et l'une de ses propriétés.

### 🐛 La série de victoires qui ne montait jamais

Tu avais écrit une fonction `update_global_variables_on_win()`, bien pensée… mais elle n'était **appelée nulle part**. La série retombait donc à 0 à chaque victoire. Même chose pour le « meilleur temps » : il partait de 0 et comparait `dernier_temps < 0`, ce qui n'arrivait jamais.

> **Leçon :** écrire une fonction, c'est bien, mais il faut vérifier qu'elle est vraiment appelée. Un `print("je passe ici")` au début d'une fonction aide beaucoup.

### 🐛 Les plantages « fantômes » en changeant d'écran

Tes animations utilisaient plein de `Clock.schedule_once(...)` qui se relancent eux-mêmes. Le problème, c'est que quand on quittait l'écran (par exemple en appuyant sur CONTINUER pendant l'animation de fin), **ces minuteurs continuaient de tourner** sur le mot suivant. Ça finissait par un plantage (`len(None)`).

> **Leçon :** tout ce que tu planifies avec `Clock`, garde-le dans une variable et annule-le (`.cancel()`) quand tu quittes l'écran. J'ai maintenant une petite méthode `later()` qui le fait automatiquement.

### 🐛 La sauvegarde fragile

Si Android fermait l'appli *pendant* l'écriture du fichier de sauvegarde, le JSON restait à moitié écrit, et l'appli plantait ensuite à chaque démarrage. Désormais, on écrit dans un fichier temporaire puis on le renomme (le renommage est instantané), et si jamais le fichier est abîmé, l'appli démarre quand même.

> **Leçon :** tout ce qui touche aux fichiers doit prévoir le cas où « ça se passe mal ».

### 🐢 Des images énormes

Tes images faisaient **1920 pixels de large, 87 Mo au total**, même les plumes affichées en tout petit. Sur un téléphone, une seule image comme ça occupe environ 20 Mo de mémoire graphique. J'ai fait un petit script (`tools/optimize_images.py`) qui les redimensionne : **1 Mo au total**, et à l'écran on ne voit aucune différence.

> **Leçon :** une image n'a jamais besoin d'être plus grande que deux fois sa taille d'affichage.

### ✂️ Le copier-coller

Le clavier faisait 1 500 lignes de `.kv` : les 36 touches étaient écrites une par une, et `grown_or_down()` répétait 72 fois la même ligne. Maintenant, le clavier est généré par une boucle à partir d'une simple chaîne `"azertyuiop"`.

> **Leçon :** si tu copies-colles la même chose plus de trois fois, c'est qu'une boucle ou une fonction t'attend.

### 📖 Quelques mots du dictionnaire

Environ 240 mots sur 578 posaient problème : des mots qui n'existent pas (`gabeloue`, `animatif`), des verbes conjugués (`chassent`, `réalisez`), des pluriels, ou des mots de 17 lettres illisibles sur un écran de téléphone. Ce n'est pas un reproche : vérifier 578 mots à la main, c'est impossible. D'où l'intérêt d'un script qui vérifie automatiquement (`tools/build_dictionary.py`).

---

## 3. Ce qui a changé

- **Le code est rangé** dans un dossier `pendu/` : la logique du jeu d'un côté (`game.py`, `events.py`…), l'affichage de l'autre (`ui/`). La logique ne dépend plus de Kivy, donc on peut la **tester automatiquement** : il y a maintenant 29 tests dans `tests/` (`python -m unittest discover tests`).
- **Un nouveau look** : bois sombre, parchemin et or, avec deux vraies polices (Cinzel Decorative pour les titres, Alegreya Sans pour le texte).
- **Un nouveau pendu** : un petit roi couronné (c'est le *Pendu Royal*, après tout !) qui apparaît pièce par pièce, s'inquiète, puis… tu verras. Tes plumes tombent en tournoyant quand on en perd une.
- **Le clavier** : plus besoin des touches accentuées. Taper `e` révèle aussi é, è, ê. Les lettres trouvées deviennent vertes, les ratées se grisent.
- **Tes 11 événements fonctionnent tous**, avec un meilleur équilibre entre bonus et pénalités.
- **Nouveaux modes** : Mode Royal (survie avec un boss tous les 5 mots), Contre-la-montre, Sans filet, et un Défi du jour.
- **Des indices** à acheter avec tes points, et la possibilité de **proposer le mot entier**.
- **Tes 9 médailles** sont devenues de vrais succès à débloquer.
- **Des sons** (générés par un script, donc sans problème de droits).
- **1 222 mots** vérifiés, chacun avec sa définition et un thème.

Au fait… le roi cache peut-être quelque chose. Observe-le bien. 👀

---

## 4. Pour la suite

Quelques pistes, si tu veux continuer à progresser :

1. **Utilise git.** Le projet en a maintenant un. Fais un commit à chaque étape qui marche : si tu casses quelque chose, tu peux revenir en arrière en une commande.
2. **Écris un test quand tu corriges un bug.** Comme ça, il ne revient jamais. Regarde `tests/test_logic.py` pour des exemples.
3. **Sépare « ce que le jeu calcule » de « ce que le jeu affiche ».** C'est la plus grosse différence entre l'ancien code et le nouveau, et c'est ce qui rend tout plus simple.
4. **Continue de dessiner et d'inventer.** Tes idées d'événements et tes illustrations, c'est la partie que personne ne peut faire à ta place.

Pour ajouter des mots : édite `tools/words_src/facile.txt` (une ligne = `mot|Thème|Définition`), puis lance `python tools/build_dictionary.py`. Le script te dira s'il y a un souci.

---

Honnêtement, beaucoup de gens abandonnent leur premier projet à la moitié. Toi, tu avais un jeu qui tournait, avec des idées originales et des dessins qui ont du style. Les erreurs ci-dessus, c'est juste l'étape suivante de l'apprentissage, et maintenant tu les connais.

Continue comme ça. 💪

---

## Crédits

- **Elmas** : correction des bugs et ajout des nouvelles fonctionnalités
- **Ilyan** : redesign complet
- **Fluxxy** : a servi à rien, mais voulait absolument être dans ce fichier 😄
