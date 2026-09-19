from keycan.utils.text import clean_source_name


def test_clean_source_name_removes_redundant_prefix_and_tag() -> None:
    assert clean_source_name("DİĞER ÇALIŞMALAR VE [DP] Örnekler") == "Örnekler"


def test_clean_source_name_keeps_meaningful_name() -> None:
    assert clean_source_name("REVERSE ENGINEERING/ 12. Python Temelleri") == "Python Temelleri"
