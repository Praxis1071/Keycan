from keycan.core.typing_engine import TypingEngine


def test_words_must_match_in_target_order() -> None:
    result = TypingEngine().match_words("alpha beta", "beta alpha")

    assert result.correctness == [False, False]
    assert result.matched_target_indices == set()


def test_word_matching_remains_case_insensitive() -> None:
    result = TypingEngine().match_words("İstanbul Linux", "istanbul linux")

    assert result.correctness == [True, True]
    assert result.matched_target_indices == {0, 1}


def test_character_matching_is_case_insensitive() -> None:
    result = TypingEngine().character_correctness("Python", "pYTHON")

    assert result == [True, True, True, True, True, True]


def test_extra_typed_characters_are_wrong() -> None:
    result = TypingEngine().character_correctness("abc", "abcx")

    assert result == [True, True, True, False]
