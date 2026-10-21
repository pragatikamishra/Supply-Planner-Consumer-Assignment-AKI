"""Chatbot brain: turns a question into SQL, runs it, and explains the result."""
import os
import re
from pathlib import Path

import ollama
import pandas as pd
import requests

from python.chatbot_db import get_schema, run_query

# Which AI to use: with a Groq key (the online app) use Groq's cloud model,
# without one (this laptop) use the local Ollama model.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
RUNS_LOCALLY = not GROQ_API_KEY

MODEL = "qwen2.5:7b"
MODEL_OPTIONS = {"temperature": 0, "num_ctx": 4096}  # 0 = same answer each time; 4096 = reading window
KEEP_ALIVE = "1h"  # keep the model in memory for an hour, so it doesn't reload

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

CONTEXT_PATH = Path("docs/business_context.md")

SQL_RULES = """You write SQLite queries for the sales database of a UAE company (year 2024, money in AED).

{schema}

Rules:
- Reply with ONE SQLite SELECT query only, no explanation.
- fact_sales joins dim_product on product_code and dim_customer on customer.
- month is text like '2024-04-01'. For April use strftime('%m', month) = '04'.
- Total sales = SUM(net_sales_aed) over all rows (sales, returns and adjustments).
- Units sold = SUM(quantity).
- Gross margin % = SUM(gross_profit_aed) * 100.0 / SUM(net_sales_aed).
- Return rate % = -(SUM of net_sales_aed where transaction_type = 'Return') * 100.0
  / (SUM of net_sales_aed where transaction_type = 'Sale').
- Round numbers to 2 decimals. For "top" or "best" questions use ORDER BY and LIMIT.
- Never add WHERE filters the question did not ask for.
- For "why" or "how" questions, break the numbers down by customer, month or transaction_type
  and show net sales, cost of sales and gross margin % (or return rate %) for each part.
"""

ANSWER_RULES = """You are SalesPilot, an AI sales and demand planning assistant for AKI Group.
Answer in up to 5 short sentences, or a short bullet list when asked for findings.
Take numbers ONLY from the query result or from the Key findings in the business context.
Always include the main numbers.
Copy numbers exactly as they are written in the result. Never recalculate or reformat them.
Numbers ending in M are millions and K are thousands; money is in AED.
For "why" or "how" questions, use the business context below to explain what the numbers mean
and end with one practical suggestion for a planner.
Only give reasons that apply to the SAME product, customer or month being asked about.
Never borrow a fact from another product (P015's below-cost problem does not apply to P105).
Say "sold below cost" only if the gross margin is negative.
If the question asks for findings, insights, a summary, recommendations or how the data
was prepared, answer from the business context.
If neither the query result nor the business context has the answer, say you don't know.

Business context:
{context}"""


REWRITE_RULES = """You rewrite follow-up questions so they make sense on their own.
Use the conversation to fill in what the user means (product, brand, customer, month or measure).
If the question already makes sense on its own, return it unchanged.
Reply with the rewritten question only."""


def load_business_context():
    """Read the dashboard findings file, so the AI can explain "why"."""
    if CONTEXT_PATH.exists():
        return CONTEXT_PATH.read_text(encoding="utf-8")
    return "No extra context available."


def warm_up():
    """Load the model into memory once, so the first question isn't slow."""
    if not RUNS_LOCALLY:
        return  # Groq's cloud model is always loaded
    ollama.generate(model=MODEL, prompt="", options=MODEL_OPTIONS, keep_alive=KEEP_ALIVE)


def ask_model(system, user):
    """Send one message to the AI (local Ollama or Groq) and return its reply text."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    if RUNS_LOCALLY:
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            options=MODEL_OPTIONS,
            keep_alive=KEEP_ALIVE,
        )
        return response["message"]["content"].strip()

    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": GROQ_MODEL, "messages": messages, "temperature": 0},
        timeout=60,
    )
    response.raise_for_status()  # stop with a clear error if Groq says no (e.g. wrong key)
    return response.json()["choices"][0]["message"]["content"].strip()


def format_number(value):
    """Write big numbers the way people read them: 91781371.77 -> 91.78M."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.2f}K"
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value:,.2f}"


def format_result(result):
    """Turn the result table into text with readable numbers for the AI."""
    if result.empty:
        return "(no query result)"
    readable = result.copy()
    for column in readable.columns:
        readable[column] = readable[column].map(format_number)
    return readable.to_string(index=False)


def extract_sql(text):
    """Pull the SQL out of the model's reply, removing ```sql fences if present."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1)
    return text.strip()


def make_standalone(question, history):
    """Turn a follow-up like "and in May?" into a full question, using the chat so far."""
    if not history:
        return question
    conversation = "\n".join(
        f"{turn['role']}: {turn['content'][:500]}" for turn in history[-6:]
    )
    return ask_model(
        REWRITE_RULES,
        f"Conversation so far:\n{conversation}\n\nFollow-up question: {question}",
    )


def ask(question, history=None):
    """Answer a question: AI writes SQL -> Python runs it -> AI explains the result."""
    question = make_standalone(question, history)
    system = SQL_RULES.replace("{schema}", get_schema())
    sql = extract_sql(ask_model(system, question))
    try:
        result = run_query(sql)
    except Exception as error:
        # Second chance: show the AI its error and let it fix the query.
        retry = (
            f"{question}\n\nYour previous query was:\n{sql}\n"
            f"It failed with this error: {error}\nWrite a corrected query."
        )
        sql = extract_sql(ask_model(system, retry))
        try:
            result = run_query(sql)
        except Exception:
            # Still failing: answer from the business context alone.
            sql = "-- No query: answered from the dashboard findings"
            result = pd.DataFrame()

    answer = ask_model(
        ANSWER_RULES.replace("{context}", load_business_context()),
        f"Question: {question}\n\nQuery result:\n{format_result(result)}",
    )
    return {"question": question, "sql": sql, "result": result, "answer": answer}


if __name__ == "__main__":
    print("Using:", f"Ollama ({MODEL})" if RUNS_LOCALLY else f"Groq ({GROQ_MODEL})")
    reply = ask("Which 3 brands had the highest total sales?")
    print("SQL used:")
    print(reply["sql"])
    print()
    print(reply["result"])
    print()
    print("Answer:", reply["answer"])