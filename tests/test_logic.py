"""Tests de la logique du jeu (sans Kivy) :  python -m unittest discover tests"""
import json
import random
import tempfile
import unittest
from datetime import date
from pathlib import Path

from pendu.achievements import unlock_new
from pendu.config import KEYBOARD_LETTERS, LEVELS
from pendu.events import ALL_EVENTS, EventDirector, roll_event
from pendu.game import ALREADY, HIT, MISS, SHIELDED, Round, Session
from pendu.storage import Profile
from pendu.words import WordBank, fold, mask_definition

EASY = LEVELS["noob"]
HARD = LEVELS["hard"]


def make_round(word="élève", level=EASY, lives=9, **kw):
    return Round({"word": word, "definition": "déf"}, level, lives, **kw)


class RoundTests(unittest.TestCase):
    def test_plain_letter_reveals_accented_variants(self):
        for level in (EASY, HARD):
            rnd = make_round("élève", level=level)
            res = rnd.guess("e")
            self.assertEqual(res.kind, HIT)
            self.assertEqual(res.positions, [0, 2, 4])
        self.assertEqual(make_round("garçon").guess("c").positions, [3])

    def test_repeat_guess_is_free(self):
        rnd = make_round("chat")
        rnd.guess("z")
        self.assertEqual(rnd.guess("z").kind, ALREADY)
        self.assertEqual(rnd.lives, 8)

    def test_win_and_loss(self):
        rnd = make_round("ab", lives=2)
        self.assertTrue(rnd.guess("a").kind == HIT and not rnd.won)
        self.assertTrue(rnd.guess("b").won)
        lost = make_round("ab", lives=2)
        lost.guess("x")
        self.assertTrue(lost.guess("y").lost)

    def test_start_reveal_never_reveals_whole_word(self):
        for seed in range(50):
            rnd = make_round("aab")
            rnd.reveal_start(0.9, random.Random(seed))
            self.assertFalse(rnd.won)

    def test_word_guess(self):
        rnd = make_round("pendu", lives=9)
        self.assertEqual(rnd.guess_word("fondu").lives_lost, 2)
        res = rnd.guess_word("PENDU")
        self.assertTrue(res.won)
        self.assertTrue(rnd.guessed_whole_word_early)
        self.assertEqual(rnd.word_guess_bonus, 50)

    def test_shield_cancels_one_error(self):
        rnd = make_round("chat")
        rnd.shield = True
        self.assertEqual(rnd.guess("z").kind, SHIELDED)
        self.assertEqual(rnd.lives, 9)
        self.assertEqual(rnd.guess("w").kind, MISS)

    def test_hints(self):
        rng = random.Random(1)
        rnd = make_round("maison")
        self.assertEqual(len(rnd.hint_eliminate(3, rng)), 3)
        for letter in rnd.eliminated:
            self.assertNotIn(letter, "maison")
            self.assertEqual(rnd.key_state(letter), "miss")
        self.assertTrue(rnd.hint_letter(rng))
        last = make_round("ab")
        last.guess("a")
        self.assertEqual(last.hint_letter(rng), [])  # jamais la dernière lettre

    def test_score_and_perfect(self):
        rnd = make_round("ab")
        rnd.guess("a"), rnd.guess("b")
        self.assertTrue(rnd.perfect)
        self.assertEqual(rnd.score(), EASY.base_score + 9 * 5 + 2 * 3)
        rnd.double_or_nothing = True
        self.assertEqual(rnd.score(), 2 * (EASY.base_score + 9 * 5 + 2 * 3))

    def test_clutch(self):
        rnd = make_round("ab", lives=2)
        rnd.guess("x"), rnd.guess("a"), rnd.guess("b")
        self.assertTrue(rnd.clutch and not rnd.perfect)


class FakeBank:
    def __init__(self):
        self.i = 0

    def pick(self, level, recent=(), rng=None):
        self.i += 1
        return {"word": f"mot{self.i}".replace("1", "a").replace("2", "b"), "definition": ""}

    def daily(self, day=None):
        return {"word": "jour", "definition": ""}


class SessionTests(unittest.TestCase):
    def test_royal_progression_and_lives(self):
        s = Session("royal", "noob", FakeBank())
        levels = [s.level_for(i) for i in range(9)]
        self.assertEqual(levels[:3], ["noob"] * 3)
        self.assertEqual(levels[-1], "hard")
        r1 = s.next_round()
        r1.lives = 4
        r1.revealed = [True] * len(r1.word)
        s.finish_round(r1)
        self.assertFalse(s.over)
        self.assertEqual(s.next_round().lives, 5)  # +1 plume par mot trouvé

    def test_classic_ends_after_one_word(self):
        s = Session("classic", "hard", FakeBank())
        s.finish_round(s.next_round())
        self.assertTrue(s.over)

    def test_hardcore_forced_settings(self):
        s = Session("hardcore", "noob", FakeBank())
        rnd = s.next_round()
        self.assertEqual((rnd.level.key, rnd.max_lives), ("hard", 3))

    def test_chrono_unlimited_lives(self):
        s = Session("chrono", "noob", FakeBank())
        rnd = s.next_round()
        for letter in "xyzwq":
            rnd.guess(letter)
        self.assertFalse(rnd.lost)
        s.chrono_penalty(2)
        self.assertEqual(s.time_left, 170)


class FakeCtx:
    def __init__(self, rnd):
        self.round = rnd
        self.calls = []

    def __getattr__(self, name):
        return lambda *a: self.calls.append((name, a))


class EventTests(unittest.TestCase):
    def test_every_event_starts_and_stops(self):
        for cls in ALL_EVENTS.values():
            ctx = FakeCtx(make_round("maison"))
            ev = cls()
            ev.start(ctx)
            ev.stop(ctx)
            self.assertIn(cls.info.kind, ("bonus", "penalty"))

    def test_roll_always_returns_an_event(self):
        rng = random.Random(3)
        kinds = {roll_event(rng).info.kind for _ in range(300)}
        self.assertEqual(kinds, {"bonus", "penalty"})

    def test_director_no_event_on_first_turn(self):
        d = EventDirector(HARD, random.Random(0))
        d.new_turn(30)
        self.assertEqual(d.triggers, [])
        d.new_turn(30)
        self.assertEqual(len(d.triggers), 3)

    def test_timed_event_ends(self):
        d = EventDirector(HARD, random.Random(0))
        ctx = FakeCtx(make_round("maison"))
        d.begin(ALL_EVENTS["hidden_timer"](), ctx)
        self.assertFalse(d.tick(5, ctx))
        self.assertTrue(d.tick(6, ctx))
        self.assertIsNone(d.active)

    def test_tax_ends_after_two_hits(self):
        rnd = make_round("maison")
        ctx = FakeCtx(rnd)
        d = EventDirector(HARD)
        d.begin(ALL_EVENTS["taxe_event"](), ctx)
        rnd.guess("z")
        self.assertEqual(rnd.tax_paid, 5)
        rnd.guess("m"), rnd.guess("a")
        self.assertTrue(d.tick(0.1, ctx))


class StorageTests(unittest.TestCase):
    def test_levels_are_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Profile(tmp)
            p.level_stats("noob")["wins"] = 5
            self.assertEqual(p.level_stats("hard")["wins"], 0)

    def test_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Profile(tmp)
            p.data["points"] = 123
            p.save()
            self.assertEqual(Profile(tmp).points, 123)
            (Path(tmp) / "user_account.json").write_text("{cassé", encoding="utf-8")
            self.assertEqual(Profile(tmp).points, 50)  # pas de plantage

    def test_migration_from_v1(self):
        old_stats = {"games_played": 4, "total_wins": 3, "total_defeates": 1, "points": 3, "best_win_steak": 2}
        old = {"language": {"french": {"level": {"noob": [old_stats], "medium": [old_stats], "hard": [old_stats]}}}}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "user_account.json").write_text(json.dumps(old), encoding="utf-8")
            p = Profile(tmp)
            self.assertEqual(p.level_stats("medium")["wins"], 3)
            self.assertEqual(p["totals"]["wins"], 9)
            self.assertEqual(p.points, 50 + 9 * 5)

    def test_streaks_and_achievements(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Profile(tmp)
            s = Session("classic", "noob", FakeBank())
            rnd = s.next_round()
            rnd.lives = 1
            rnd.revealed = [True] * len(rnd.word)
            pts = s.finish_round(rnd)
            p.record_round(rnd, pts, 12.0, count_level_stats=True)
            stats = p.level_stats("noob")
            self.assertEqual((stats["wins"], stats["streak"], stats["clutch"]), (1, 1, 1))
            self.assertEqual(stats["best_time"], 12.0)
            new = [a.key for a in unlock_new(p.data, s)]
            self.assertIn("miracule", new)
            self.assertEqual(unlock_new(p.data, s), [])

    def test_daily_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Profile(tmp)
            for day in (date(2026, 9, 1), date(2026, 9, 2)):
                s = Session("daily", "noob", FakeBank(), today=day)
                rnd = s.next_round()
                rnd.revealed = [True] * len(rnd.word)
                s.finish_round(rnd)
                p.record_session(s)
            self.assertEqual(p["modes"]["daily"]["streak"], 2)
            self.assertTrue(p.daily_done(date(2026, 9, 2)))


class WordTests(unittest.TestCase):
    def test_fold_and_mask(self):
        self.assertEqual(fold("çà et là, élève"), "ca et la, eleve")
        self.assertEqual(mask_definition("Un éléphant et des éléphanteaux.", "éléphant"),
                         "Un ____ et des ____.")

    def test_dictionary_is_playable(self):
        bank = WordBank()
        seen = set()
        for level, entries in bank.words.items():
            self.assertGreaterEqual(len(entries), 300, level)
            for e in entries:
                w = e["word"]
                self.assertTrue(set(fold(w)) <= KEYBOARD_LETTERS, w)  # jouable au clavier
                self.assertLessEqual(len(w), 12, w)                    # tient sur une ligne
                self.assertTrue(e["definition"] and e["theme"], w)
                self.assertNotIn(w, seen)
                seen.add(w)

    def test_bank_pick_and_daily(self):
        bank = WordBank()
        recent = [e["word"] for e in bank.words["noob"][:-1]]
        self.assertEqual(bank.pick("noob", recent)["word"], bank.words["noob"][-1]["word"])
        self.assertEqual(bank.daily(date(2026, 1, 1)), bank.daily(date(2026, 1, 1)))


if __name__ == "__main__":
    unittest.main()
