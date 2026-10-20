# Sales Data Pipeline → Power BI

An ETL pipeline that takes 2024 sales data from Google Sheets, checks and cleans it,
loads it into a database, and feeds a Power BI dashboard.

Google Sheets → Extract → Transform → Load (SQLite) → Power BI (ODBC)

## Run it

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python main.py

Then open `powerbi/sales_dashboard.pbix` and click Refresh.

## Steps

| Step        | File                                          | What it does                                                               |
| ----------- | --------------------------------------------- | -------------------------------------------------------------------------- |
| Extract     | python/extract.py                             | Downloads the sales, product and customer tabs into data/raw, untouched    |
| Profile     | python/profile_data.py, python/deep_checks.py | Measures data quality; findings in docs/data_checks.md                     |
| Transform   | python/transform.py                           | Applies the cleaning decisions; bad rows go to data/rejected with a reason |
| Load        | python/load.py, sql/schema.sql                | Rebuilds a star schema in SQLite and verifies row counts                   |
| Orchestrate | main.py                                       | Runs all steps in order and logs each run to logs/                         |

## Data model (star schema)

- fact_sales: one row per month, customer and product (160,564 rows)
- dim_product: 250 products
- dim_customer: 292 customers

## Results of the latest run

160,572 sales rows extracted, 160,564 loaded, 8 rejected (quantity and value had opposite signs).


## AI chatbot (bonus)

A chat page where anyone can ask questions about the sales data in plain English, for example
*"Which 5 customers bought the most?"* or *"What was the gross margin % in April?"*

**How it works**

1. The question goes to a local AI model (**Qwen 2.5 7B via Ollama**) together with the database schema
   and the business rules (the same formulas as the Power BI measures).
2. The AI writes a SQL query. Python runs it on `data/sales.db`, **the same database Power BI uses**,
   so the chatbot and the dashboard always agree.
3. The result goes back to the AI, which answers in 1-3 sentences. Under every answer,
   *"How I got this answer"* shows the SQL and the data, so every number can be checked.

**Design choices**

| Choice                                              | Why                                                                 |
| --------------------------------------------------- | ------------------------------------------------------------------- |
| Local model (Ollama)                                | Free, works offline, and company data never leaves the machine      |
| Read-only database connection, `SELECT` only      | The AI can never change or delete data                              |
| Python formats the numbers, the AI only copies them | Small AI models make mistakes when converting numbers (e.g. 91.78M) |
| One automatic retry with the error message          | The AI can fix its own SQL mistakes                                 |
| `temperature = 0`                                 | The same question gives the same answer                             |

**Run it**

1. Install Ollama from [ollama.com](https://ollama.com) and download the model: `ollama pull qwen2.5:7b`
2. Activate the venv and install the libraries: `pip install -r requirements.txt`
3. Run the pipeline once so `data/sales.db` exists: `python main.py`
4. Start the chat page: `streamlit run app.py`, then open http://localhost:8501

| File                       | Role                                           |
| -------------------------- | ---------------------------------------------- |
| `app.py`                 | Streamlit chat page                            |
| `python/chatbot.py`      | Question -> SQL -> answer                      |
| `python/chatbot_db.py`   | Describes the tables and runs read-only SQL    |
| `.streamlit/config.toml` | AKI colours, localhost only, no usage tracking |
