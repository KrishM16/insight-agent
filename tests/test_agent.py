from app.agent import _clean_sql


def test_strips_markdown_fence():
    assert _clean_sql("```sql\nSELECT 1\n```") == "SELECT 1"


def test_strips_leading_prose():
    assert _clean_sql("Here you go:\nSELECT a FROM b;") == "SELECT a FROM b"


def test_keeps_cte():
    assert _clean_sql("WITH x AS (SELECT 1) SELECT * FROM x").startswith("WITH")
