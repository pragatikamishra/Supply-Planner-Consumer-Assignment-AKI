"""Chatbot brain: turns a question into SQL, runs it, and explains the result."""
import re

import ollama

from python.chatbot_db import get_schema, run_query

MODEL = "qwen2.5:7b"

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
"""

ANSWER_RULES = """You are SalesPilot, an AI sales and demand planning assistant for AKI Group.
Answer the question in 1 to 3 short sentences using ONLY the query result you are given.
Always include the main numbers from the result in your answer.
Copy numbers exactly as they are written in the result. Never recalculate or reformat them.
Numbers ending in M are millions and K are thousands; money is in AED.
If the result is empty, say that no data was found."""


def ask_model(system, user):
    """Send one message to the local Ollama model and return its reply text."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0},  # 0 = same question, same answer
    )
    return response["message"]["content"].strip()


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


def ask(question):
    """Answer a question: AI writes SQL -> Python runs it -> AI explains the result."""
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
        result = run_query(sql)

    answer = ask_model(
        ANSWER_RULES,
        f"Question: {question}\n\nQuery result:\n{format_result(result)}",
    )
    return {"sql": sql, "result": result, "answer": answer}


if __name__ == "__main__":
    reply = ask("Which 3 brands had the highest total sales?")
    print("SQL used:")
    print(reply["sql"])
    print()
    print(reply["result"])
    print()
    print("Answer:", reply["answer"])