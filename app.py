import streamlit as st
import json
import random
from similarity import SimilarityRouter

from tools import (
    get_market_price,
    search_research_papers,
    get_currency_rate,
    describe_research_paper
)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Buddy AI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Buddy - Smart Tool Assistant")
st.caption("Ask about stocks, gold/silver, or research papers")

# ---------------- LOAD PERSONALITY ----------------
@st.cache_resource
def load_personality():
    with open("personality.json", "r") as f:
        personality = json.load(f)
    router = SimilarityRouter(personality["examples"])
    return personality, router

personality, router = load_personality()

# ---------------- SESSION MEMORY ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- UTIL FUNCTIONS ----------------
def detect_tool(user_input: str):
    text = user_input.lower()

    for tool_name, keywords in personality["tool_rules"].items():
        if any(keyword in text for keyword in keywords):
            return tool_name
    return None


def pick_random(key: str):
    return random.choice(personality[key])


def get_name():
    return random.choice(personality["names"])


# ---------------- DISPLAY CHAT HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ---------------- USER INPUT ----------------
@st.cache_data(show_spinner=False)
def cached_paper_search(query: str):
    return search_research_papers.invoke(query)

@st.cache_data(show_spinner=False)
def cached_paper_detail(query: str):
    return describe_research_paper.invoke(query)

user_input = st.chat_input("Ask me anything...")

if user_input:

    # show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # personality generation
    name = get_name()
    greeting = pick_random("greetings").format(name=name)
    filler = pick_random("fillers")
    signoff = pick_random("sign_offs").format(name=name)

    # TOOL ROUTING
    tool = router.route(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking... 🧠"):

            if tool == "market":
                result = get_market_price.invoke(user_input)

            elif tool == "currency":
                result = get_currency_rate.invoke(user_input)

            elif tool == "scholar":
                result = search_research_papers.invoke(user_input)

            elif tool == "paper_detail":
                result = describe_research_paper.invoke(user_input)

            else:
                result = (
                    "Hmm Buddy 🤔 I couldn’t match that clearly.\n"
                    "Try asking about gold prices, currency exchange, or research papers."
                )

            max_len = personality.get("max_context_chars", 1200)

            final_response = f"""
**{greeting}**

{filler}

{result[:max_len]}

*{signoff}*
"""

            st.markdown(final_response)

    # save bot message
    st.session_state.messages.append(
        {"role": "assistant", "content": final_response}
    )