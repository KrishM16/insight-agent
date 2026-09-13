# InsightAgent

Natural language questions against a relational database, answered by a LangGraph
agent that writes SQL, executes it, and self-corrects on failure.

## Results

| metric | value |
|---|---|
| execution accuracy | 21/22 (95.5%) |
| refusal on unanswerable questions | 3/3 |
| refusal before the answerability gate | 0/3 |
| avg latency | 6.1s |

Measured by `python -m evals.run_eval` against 25 gold questions.

## Why an agent and not a single prompt

Three decisions the graph makes that a single LLM call cannot:

1. **Answerability gate.** Before writing SQL, the agent checks whether the
   question is answerable from the columns that exist. Without it, the model
   answered all three unanswerable questions by inventing columns: it aliased
   `unit_price` as `profit_margin`, and derived a "satisfaction score" from
   order status. Adding the gate took hallucinated answers from 3/3 to 0/3.
2. **Execute-and-retry.** SQL runs against the real database; the error text is
   fed back into the prompt for up to two retries. Capped, because an
   unanswerable question otherwise loops forever.
3. **Read-only enforcement.** Model output never reaches the database
   unguarded. Non-SELECT statements are rejected before execution.

## How correctness is measured

Comparing SQL strings does not work: `COUNT(*)` and `COUNT(1)` differ as text
and agree as answers. So both the agent's query and a reference query are
executed and their **result sets** compared, order-insensitively and with float
tolerance. This is execution accuracy, the standard text-to-SQL metric.

The eval reports three numbers separately: baseline accuracy, accuracy on hard
cases (multi-hop joins, time windows, ratio denominators), and refusal rate on
questions the schema cannot answer. Refusal is scored separately because a
confidently wrong number is worse than no answer.

## The one failing case, deliberately

"Which region has the highest revenue per customer, counting only customers who
ordered?" The agent divides by customers who ordered; the reference divides by
all customers in the region. Both readings are defensible. It is kept as a
failure because a suite at 100% has stopped detecting anything, and because
ambiguous metric definitions are the realistic failure mode in analytics work.

## Known limitations

- The answerability gate is a second LLM call per question, roughly doubling
  latency. A cheaper schema-keyword pre-filter would cut this.
- Single database, SQLite. No cross-database joins or dialect handling.
- Retry uses the raw database error; it does not reason about why a join
  produced the wrong grain.

## Stack

FastAPI, LangGraph, LangChain, SQLite, Pydantic, pytest.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo 'GROQ_API_KEY=your_key' > .env
python seed_db.py
uvicorn app.main:app --reload    # http://127.0.0.1:8000/docs
python -m evals.run_eval
pytest -q
```
