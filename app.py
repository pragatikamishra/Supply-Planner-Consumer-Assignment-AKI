"""AKI Sales Assistant: a chat page that answers questions about the sales database."""
import streamlit as st

from python.chatbot import ask

st.set_page_config(page_title="AKI Sales Assistant", page_icon="💬")
st.title("AKI Sales Assistant")
st.caption("Ask about 2024 sales. The AI runs on this computer, so the data never leaves it.")

with st.sidebar:
    st.header("Try asking")
    st.markdown(
        "- Which 5 customers bought the most?\n"
        "- What was the gross margin % in April?\n"
        "- Which division has the highest return rate?\n"
        "- Show total sales by month"
    )

# The chat history lives in session_state, so it survives each page refresh.
if "messages" not in st.session_state:
    st.session_state.messages = []


def number_formats(table):
    """Show numbers with thousand separators, e.g. 41,947,356.53."""
    return {
        column: st.column_config.NumberColumn(format="localized")
        for column in table.select_dtypes("number").columns
    }


def show(message):
    """Draw one chat bubble, plus the SQL and data behind an answer."""
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "sql" in message:
            with st.expander("How I got this answer"):
                st.code(message["sql"], language="sql")
                st.dataframe(
                    message["result"],
                    hide_index=True,
                    column_config=number_formats(message["result"]),
                )


for message in st.session_state.messages:
    show(message)

question = st.chat_input("Ask about sales, brands, customers...")
if question:
    user_message = {"role": "user", "content": question}
    st.session_state.messages.append(user_message)
    show(user_message)

    with st.spinner("Thinking..."):
        try:
            reply = ask(question)
            bot_message = {
                "role": "assistant",
                "content": reply["answer"],
                "sql": reply["sql"],
                "result": reply["result"],
            }
        except Exception as error:
            bot_message = {
                "role": "assistant",
                "content": f"Sorry, I couldn't answer that. Try rephrasing it. ({error})",
            }
    st.session_state.messages.append(bot_message)
    show(bot_message)