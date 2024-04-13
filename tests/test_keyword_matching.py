from unittest import TestCase

from core.resources.controllers import contains_keyword, text_matches, detect_spam_evading
from core.resources.enums import IgnoreReason
from core.utils.result import Ok, Err

from typing_extensions import assert_never  # python < 3.11


class TestKeywordMatching(TestCase):
    text = "AbacABA one two three"

    def test_contains_keyword(self):
        seq = ["two"]
        self.assertEqual(contains_keyword(self.text, seq), seq[0])
        self.assertIsNone(contains_keyword(self.text, ["qwerty"]))

        seq_2 = ["ThreE"]
        self.assertEqual(contains_keyword(self.text, seq_2), seq_2[0])

        seq_3 = ["abacaba"]
        self.assertEqual(contains_keyword(self.text, seq_3), seq_3[0])

        seq_4 = ["|wo"]
        self.assertIsNone(contains_keyword(self.text, seq_4))

        self.assertEqual(contains_keyword('one wo thre', seq_4), 'wo')

    def test_text_matches(self):
        self.assertEqual(text_matches(self.text, ["bac"], ["qwertyu"]), Ok("bac"))
        self.assertEqual(text_matches(self.text, ["bac"], ["caba"]), Err(IgnoreReason.MINUS_WORD_MATCH))
        self.assertEqual(text_matches(self.text, ["cacabac"], []), Err(IgnoreReason.NO_MATCH))

        # Mixed characters from Latin and Cyrillic
        self.assertEqual(text_matches("АБВabc", ["abc"], []), Err(IgnoreReason.SPAM_EVADING_MATCH))

    def test_match_case(self):
        match res := text_matches(self.text, ["bac"], ["qwertyu"]):
            case Ok(keyword):
                self.assertEqual(keyword, "bac")
            case _:
                assert_never(res)

    def test_detect_spam_evading(self):
        self.assertTrue(detect_spam_evading("АБВabc"))
        self.assertFalse(detect_spam_evading("abc"))
        self.assertFalse(detect_spam_evading("АБВ"))
        self.assertFalse(detect_spam_evading("АБВ abc"))
        self.assertFalse(detect_spam_evading(""))
