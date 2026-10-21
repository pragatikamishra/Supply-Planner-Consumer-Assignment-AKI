"""SalesPilot: a chat page that answers questions about AKI sales data."""
import streamlit as st

from python import extract, load, transform
from python.chatbot import GROQ_API_KEY, ask
from python.config import DB_PATH

st.set_page_config(page_title="SalesPilot", page_icon="📈")


# All chats live in session_state: a list of chats, each chat a list of messages.
# Each visitor has their own chats, so nobody sees anyone else's questions.
if "chats" not in st.session_state:
    st.session_state.chats = [[]]
    st.session_state.current = 0


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
def prepare_data():
    """Runs once when the app starts: builds sales.db with the pipeline if it's missing."""
    if not DB_PATH.exists():
        load.run(transform.run(extract.run()))
    return True


st.title("📈 SalesPilot")
st.subheader("Turn data into understandable answers")
st.caption(
    "Ask about AKI's 2024 sales, products and customers. "
    "Answers come from the same database as the Power BI dashboard."
)

if not GROQ_API_KEY:
    st.error("No Groq API key found. Add GROQ_API_KEY to .streamlit/secrets.toml and restart.")
    st.stop()

with st.spinner("Preparing the sales data (first start only, about 20 seconds)..."):
    prepare_data()

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
    show(bot_message)
    if len(messages) == 2:
        st.rerun()  # first answer in a new chat: refresh so it appears in the sidebar