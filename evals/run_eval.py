"""Execution accuracy on answerable questions + refusal rate on unanswerable ones."""
import time, json
from app.db import run_sql
from app.agent import answer_question
from evals.gold import GOLD
from evals.gold_hard import HARD, UNANSWERABLE


def normalize(rows):
    out = []
    for row in rows:
        out.append(tuple(round(v, 2) if isinstance(v, float) else v for v in row))
    return sorted(out, key=str)


def score_set(name, cases):
    passed, records = 0, []
    print(f"\n=== {name} ===")
    for question, gold_sql in cases:
        expected = run_sql(gold_sql)
        t0 = time.time()
        try:
            got = answer_question(question)
            actual = run_sql(got["sql"])
            ok = actual["error"] is None and normalize(actual["rows"]) == normalize(expected["rows"])
        except Exception as e:
            got, actual, ok = {"sql": None, "attempts": 0}, {"error": str(e), "rows": []}, False
        lat = round(time.time() - t0, 2)
        passed += ok
        records.append({"set": name, "question": question, "pass": ok,
                        "attempts": got.get("attempts"), "latency_s": lat,
                        "agent_sql": got.get("sql"), "expected_rows": expected["rows"],
                        "actual_rows": actual.get("rows"), "error": actual.get("error")})
        print(f"{'PASS' if ok else 'FAIL'}  {lat:>5}s  {question}")
        if not ok:
            print(f"      expected {expected['rows']}")
            print(f"      got      {actual.get('rows')}  err={actual.get('error')}")
    return passed, records


def score_refusals():
    print("\n=== unanswerable ===")
    refused, records = 0, []
    for q in UNANSWERABLE:
        got = answer_question(q)
        result = run_sql(got["sql"]) if got["sql"] else {"error": "no sql"}
        # Correct behaviour: the SQL errors out or the answer admits it cannot be found.
        ok = result["error"] is not None or any(
            s in got["answer"].lower() for s in ["cannot", "can't", "not available", "no data", "does not"])
        refused += ok
        records.append({"set": "unanswerable", "question": q, "pass": ok,
                        "agent_sql": got.get("sql"), "answer": got.get("answer")})
        print(f"{'PASS' if ok else 'FAIL'}  {q}")
        if not ok:
            print(f"      hallucinated: {got.get('sql')}")
    return refused, records


if __name__ == "__main__":
    p1, r1 = score_set("baseline", GOLD)
    p2, r2 = score_set("hard", HARD)
    p3, r3 = score_refusals()

    all_r = r1 + r2 + r3
    ans_total = len(GOLD) + len(HARD)
    ans_pass = p1 + p2
    lat = [r["latency_s"] for r in all_r if r.get("latency_s")]

    print(f"\nbaseline      {p1}/{len(GOLD)}")
    print(f"hard          {p2}/{len(HARD)}")
    print(f"overall exec accuracy  {ans_pass}/{ans_total} = {round(100*ans_pass/ans_total,1)}%")
    print(f"refusal on unanswerable {p3}/{len(UNANSWERABLE)}")
    print(f"avg latency   {round(sum(lat)/len(lat),2)}s")

    json.dump({"exec_accuracy_pct": round(100*ans_pass/ans_total,1),
               "baseline": f"{p1}/{len(GOLD)}", "hard": f"{p2}/{len(HARD)}",
               "refusal": f"{p3}/{len(UNANSWERABLE)}",
               "avg_latency_s": round(sum(lat)/len(lat),2), "records": all_r},
              open("evals/results.json","w"), indent=2, default=str)
    print("Wrote evals/results.json")
