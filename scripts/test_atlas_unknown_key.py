import unittest

from build_musia_atlas_study_data import number_note_for_midi


class AtlasKeyTests(unittest.TestCase):
    def test_unverified_key_does_not_invent_c_major(self):
        self.assertEqual(number_note_for_midi(67, "Unverified"), "")
        self.assertEqual(number_note_for_midi(67, ""), "")

    def test_known_tonic(self):
        self.assertEqual(number_note_for_midi(67, "G major"), "1")
        self.assertEqual(number_note_for_midi(60, "C major"), "1")


if __name__ == "__main__":
    unittest.main()
