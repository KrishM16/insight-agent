import re
from typing import TypedDict, Optional, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from app.db import get_schema, run_sql

load_dotenv()
MAX_RETRIES = 2

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

CONVENTIONS = (
    "Conventions:\n"
    "- Express any rate, share, or percentage as a number between 0 and 100, rounded to 2 decimals.\n"
    "- Always return the metric being asked about as a column alongside its label.\n"
    "  For 'which X has the highest Y', return both X and Y.\n"
    "- Do not include ID columns unless the question asks for an ID.\n"
    "- Dates are TEXT in YYYY-MM-DD format.\n"
    "- Use only SELECT."
)


class AgentState(TypedDict):
    question: str
    schema: str
    answerable: Optional[bool]
    reason: Optional[str]
    sql: Optional[str]
    result: Optional[dict[str, Any]]
    error: Optional[str]
    attempts: int
    answer: Optional[str]


def _clean_sql(text: str) -> str:
    text = re.sub(r"```(?:sql)?", "", text).strip()
    m = re.search(r"(SELECT|WITH)\b.*", text, re.I | re.S)
    return m.group(0).strip().rstrip(";") if m else text


def check_answerable(state: AgentState) -> AgentState:
    """Gate: can this question be answered from the columns that actually exist?"""
    prompt = (
        f"Schema:\n{state['schema']}\n\n"
        f"Question: {state['question']}\n\n"
        "Can this be answered using ONLY the columns above? A column that merely "
        "sounds similar does not count. Cost, profit, satisfaction, marketing channel, "
        "and ratings are NOT present unless literally listed.\n"
        "Reply exactly 'YES' or 'NO: <which data is missing>'."
    )
    verdict = llm.invoke(prompt).content.strip()
    ok = verdict.upper().startswith("YES")
    return {**state, "answerable": ok, "reason": None if ok else verdict.lstrip("NO:").strip()}


def route_gate(state: AgentState) -> str:
    return "write_sql" if state["answerable"] else "refuse"


def refuse(state: AgentState) -> AgentState:
    return {**state,
            "sql": None,
            "answer": f"I cannot answer that from this database. Missing data: {state['reason']}"}


def write_sql(state: AgentState) -> AgentState:
    retry = ""
    if state["error"]:
        retry = (f"\nYour previous query failed.\nQuery: {state['sql']}\n"
                 f"Error: {state['error']}\nFix it and return corrected SQL only.")
    prompt = (
        f"You write SQLite SELECT queries.\n\nSchema:\n{state['schema']}\n\n"
        f"{CONVENTIONS}\n\nQuestion: {state['question']}{retry}\n\n"
        "Return ONLY the SQL. No explanation, no markdown."
    )
    return {**state, "sql": _clean_sql(llm.invoke(prompt).content),
            "attempts": state["attempts"] + 1}


def execute_sql(state: AgentState) -> AgentState:
    res = run_sql(state["sql"])
    return {**state, "result": res, "error": res["error"]}


def should_retry(state: AgentState) -> str:
    return "retry" if state["error"] and state["attempts"] <= MAX_RETRIES else "answer"


def summarize(state: AgentState) -> AgentState:
    if state["error"]:
        return {**state, "answer": f"Could not answer after {state['attempts']} attempts. "
                                   f"Last error: {state['error']}"}
    r = state["result"]
    prompt = (f"Question: {state['question']}\nSQL run: {state['sql']}\n"
              f"Columns: {r['columns']}\nRows: {r['rows']}\n\n"
              "Answer in two sentences using only these rows. Include the actual "
              "numbers. Do not mention SQL.")
    return {**state, "answer": llm.invoke(prompt).content.strip()}


def build_graph():
    g = StateGraph(AgentState)
    for name, fn in [("check", check_answerable), ("refuse", refuse),
                     ("write_sql", write_sql), ("execute_sql", execute_sql),
                     ("summarize", summarize)]:
        g.add_node(name, fn)
    g.set_entry_point("check")
    g.add_conditional_edges("check", route_gate,
                            {"write_sql": "write_sql", "refuse": "refuse"})
    g.add_edge("refuse", END)
    g.add_edge("write_sql", "execute_sql")
    g.add_conditional_edges("execute_sql", should_retry,
                            {"retry": "write_sql", "answer": "summarize"})
    g.add_edge("summarize", END)
    return g.compile()


GRAPH = build_graph()


def answer_question(question: str) -> dict[str, Any]:
    f = GRAPH.invoke({"question": question, "schema": get_schema(), "answerable": None,
                      "reason": None, "sql": None, "result": None, "error": None,
                      "attempts": 0, "answer": None})
    return {"sql": f["sql"], "answer": f["answer"], "attempts": f["attempts"],
            "answerable": f["answerable"]}
