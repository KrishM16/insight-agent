from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from app.agent import answer_question

app = FastAPI(title="InsightAgent")

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    question: str
    sql: Optional[str] = None
    answer: str
    attempts: int

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    out = answer_question(req.question)
    return AskResponse(question=req.question, **out)
