from app.db import run_sql, get_schema


def test_schema_lists_all_tables():
    s = get_schema()
    assert "customers" in s and "orders" in s and "products" in s


def test_select_works():
    r = run_sql("SELECT COUNT(*) FROM orders")
    assert r["error"] is None and r["rows"][0][0] == 8000


def test_write_is_blocked():
    r = run_sql("DROP TABLE orders")
    assert r["error"] is not None
    assert run_sql("SELECT COUNT(*) FROM orders")["rows"][0][0] == 8000


def test_invalid_sql_returns_error_not_crash():
    r = run_sql("SELECT nope FROM orders")
    assert r["error"] is not None
