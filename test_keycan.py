#!/usr/bin/env python3
"""Keycan'ın kritik, saf yardımcı fonksiyonları için hızlı regresyon testleri."""

import unittest

from main import format_remaining, natural_sort_key, normalize_word


class KeycanCoreTests(unittest.TestCase):
    def test_normalize_word_ignores_case_and_punctuation(self) -> None:
        self.assertEqual(normalize_word("Gittim,"), "gittim")
        self.assertEqual(normalize_word("GİTTİM!"), "gittim")
        self.assertEqual(normalize_word("Türkçe…"), "türkçe")

    def test_normalize_word_keeps_letters_and_numbers(self) -> None:
        self.assertEqual(normalize_word("A1-B2"), "a1b2")

    def test_format_remaining_rounds_up_visible_fraction(self) -> None:
        self.assertEqual(format_remaining(60), "01:00")
        self.assertEqual(format_remaining(59.01), "01:00")
        self.assertEqual(format_remaining(0), "00:00")
        self.assertEqual(format_remaining(-1), "00:00")

    def test_natural_sort_places_numeric_names_in_numeric_order(self) -> None:
        names = ["Ders 10", "Ders 2", "Ders 1"]
        self.assertEqual(sorted(names, key=natural_sort_key), ["Ders 1", "Ders 2", "Ders 10"])


if __name__ == "__main__":
    unittest.main()
