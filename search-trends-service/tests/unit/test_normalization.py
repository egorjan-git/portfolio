from search_trends.domain.normalization import normalize_query, query_tokens


def test_normalize_query() -> None:
    assert normalize_query("  Смартфон   SAMSUNG  ") == "смартфон samsung"


def test_query_tokens() -> None:
    assert query_tokens("iphone-15 pro max") == {"iphone-15", "pro", "max"}
