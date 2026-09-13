import sqlite3, re
from typing import Any

DB_PATH = "retail.db"

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b", re.I)

def get_schema() -> str:
    """Return a compact text description of every table and column."""
    con = sqlite3.connect(DB_PATH)
    lines = []
    tables = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    for (table,) in tables:
        cols = con.execute(f"PRAGMA table_info({table})").fetchall()
        col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
        sample = con.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        lines.append(f"TABLE {table}({col_desc})\n  example row: {sample}")
    con.close()
    return "\n".join(lines)

def run_sql(sql: str, max_rows: int = 50) -> dict[str, Any]:
    """Run a read-only query. Returns columns, rows, and any error."""
    if FORBIDDEN.search(sql):
        return {"error": "Only SELECT queries are allowed.", "columns": [], "rows": []}
    con = sqlite3.connect(DB_PATH)
    try:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
        return {"error": None, "columns": cols, "rows": rows}
    except Exception as e:
        return {"error": str(e), "columns": [], "rows": []}
    finally:
        con.close()
