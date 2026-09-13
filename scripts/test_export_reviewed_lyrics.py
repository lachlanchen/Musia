#!/usr/bin/env python3
import unittest

from export_reviewed_lyrics import map_words


class ReviewedAnchorTests(unittest.TestCase):
    def test_source_close_spelling_preserves_word_anchors(self):
        segment = {"start": 1.1, "text": "伴手", "words": [
            {"word": "伴", "start": 1.0, "end": 1.5},
            {"word": "手", "start": 1.5, "end": 2.0}]}
        tokens = map_words(segment, "半首")
        self.assertEqual([t["text"] for t in tokens], ["半", "首"])
        self.assertEqual([t["start"] for t in tokens], [1.0, 1.5])

    def test_rejects_invented_missing_word_alignment(self):
        with self.assertRaisesRegex(ValueError, "re-alignment"):
            map_words({"text": "半", "words": [{"word": "半", "start": 1, "end": 2}]}, "半首")

    def test_rejects_zero_duration_hallucinated_word(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            map_words({"text": "半", "words": [{"word": "半", "start": 1, "end": 1}]}, "半")

    def test_explicit_review_can_restore_asr_merged_name_without_new_timestamps(self):
        segment = {"text": "肠", "words": [{"word": "肠", "start": 1, "end": 2}]}
        tokens = map_words(segment, "长安", {"0": {"source": "肠", "text": "长安",
                           "reason": "Independent transcript supports the slurred proper name."}})
        self.assertEqual(tokens[0]["text"], "长安")
        self.assertEqual((tokens[0]["start"], tokens[0]["end"]), (1, 2))
        self.assertEqual(tokens[0]["sourceText"], "肠")

    def test_override_must_match_evidence(self):
        with self.assertRaisesRegex(ValueError, "source evidence"):
            map_words({"words": [{"word": "肠", "start": 1, "end": 2}]}, "长安",
                      {"0": {"source": "其他", "text": "长安", "reason": "reviewed"}})


if __name__ == "__main__":
    unittest.main()
