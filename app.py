"""SalesPilot: a chat page that answers questions about AKI sales data."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from python.chatbot import ask, warm_up

CHATS_FILE = Path("chats/history.json")  # saved chats, so they survive a restart

st.set_page_config(page_title="SalesPilot", page_icon="📈")


def load_chats():
    """Read saved chats from disk; result tables are turned back into DataFrames."""
    if not CHATS_FILE.exists():
        return []
    chats = json.loads(CHATS_FILE.read_text(encoding="utf-8"))
    for chat in chats:
        for message in chat:
            if "result" in message:
                message["result"] = pd.DataFrame(message["result"])
    return chats


def save_chats():
    """Write all chats to disk; result tables are stored as plain rows."""
    saved = []
    for chat in st.session_state.chats:
        if not chat:
            continue
        saved.append([
            {**m, "result": json.loads(m["result"].to_json(orient="records"))}
            if "result" in m else m
            for m in chat
        ])
    CHATS_FILE.parent.mkdir(exist_ok=True)
    CHATS_FILE.write_text(json.dumps(saved, indent=1), encoding="utf-8")


# All chats live in session_state: a list of chats, each chat a list of messages.
# The app always opens on a fresh, empty chat; old chats are in the sidebar.
if "chats" not in st.session_state:
    st.session_state.chats = load_chats() + [[]]
    st.session_state.current = len(st.session_state.chats) - 1


SUGGESTED_QUESTIONS = [
    "What are the key findings?",
    "Show units sold by month",
    "Which 10 products sold the most units?",
    "Which division has the highest return rate?",
    "Which 5 customers bought the most?",
    "What was the gross margin % in April?",
    "Why does product P015 have a negative gross margin?",
    "What do you recommend?",
]


def ask_suggested():
    """When a question is picked in the dropdown, send it and reset the dropdown."""
    st.session_state.pending_question = st.session_state.suggested
    st.session_state.suggested = None


def chat_title(chat):
    """Name a chat after its first question, like ChatGPT does."""
    first_question = next(m["content"] for m in chat if m["role"] == "user")
    return first_question[:35] + ("..." if len(first_question) > 35 else "")


with st.sidebar:
    if st.button("➕ New chat", width="stretch"):
        if st.session_state.chats[st.session_state.current]:  # don't stack empty chats
            st.session_state.chats.append([])
            st.session_state.current = len(st.session_state.chats) - 1
        st.rerun()

    st.header("Try asking")
    st.selectbox(
        "Suggested questions",
        SUGGESTED_QUESTIONS,
        index=None,
        placeholder="Pick a question...",
        key="suggested",
        on_change=ask_suggested,
        label_visibility="collapsed",
    )

    st.header("Your chats")
    for number in reversed(range(len(st.session_state.chats))):
        chat = st.session_state.chats[number]
        if not chat:
            continue
        is_open = number == st.session_state.current
        if st.button(
            chat_title(chat),
            key=f"chat_{number}",
            type="primary" if is_open else "secondary",
            width="stretch",
        ):
            st.session_state.current = number
            st.rerun()


@st.cache_resource
def load_model():
    """Runs once when the app starts: loads the AI model into memory."""
    warm_up()
    return True


st.title("📈 SalesPilot")
st.subheader("Turn data into understandable answers")
st.caption(
    "Ask about AKI's 2024 sales, products and customers. "
    "The AI runs on this computer, so the data never leaves it."
)

with st.spinner("Loading SalesPilot's AI model..."):
    load_model()

messages = st.session_state.chats[st.session_state.current]


def number_formats(table):
    """Show numbers with thousand separators, e.g. 41,947,356.53."""
    return {
        column: st.column_config.NumberColumn(format="localized")
        for column in table.select_dtypes("number").columns
    }


def show(message):
    """Draw one chat bubble, plus the SQL and data behind an answer."""
    avatar = "📈" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])
        if "sql" in message:
            with st.expander("How I got this answer"):
                if "question" in message:
                    st.caption(f"I understood the question as: {message['question']}")
                st.code(message["sql"], language="sql")
                st.dataframe(
                    message["result"],
                    hide_index=True,
                    column_config=number_formats(message["result"]),
                )


for message in messages:
    show(message)

question = st.chat_input("Ask SalesPilot about sales, products, customers...")
question = question or st.session_state.pop("pending_question", None)
if question:
    # Earlier messages of this chat, so SalesPilot understands follow-up questions.
    history = [{"role": m["role"], "content": m["content"]} for m in messages]
    user_message = {"role": "user", "content": question}
    messages.append(user_message)
    show(user_message)

    with st.spinner("SalesPilot is thinking..."):
        try:
            reply = ask(question, history)
            bot_message = {
                "role": "assistant",
                "content": reply["answer"],
                "question": reply["question"],
                "sql": reply["sql"],
                "result": reply["result"],
            }
        except Exception as error:
            bot_message = {
                "role": "assistant",
                "content": f"Sorry, I couldn't answer that. Try rephrasing it. ({error})",
            }
    messages.append(bot_message)
    save_chats()
    show(bot_message)
    if len(messages) == 2:
        st.rerun()  # first answer in a new chat: refresh so it appears in the sidebar