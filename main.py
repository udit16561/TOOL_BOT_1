import json
import random
from similarity import SimilarityRouter


from tools import (
    get_market_price,
    search_research_papers,
    get_currency_rate,
    describe_research_paper
)

# ---------------- LOAD PERSONALITY ----------------
with open("personality.json", "r") as f:
    personality = json.load(f)

router = SimilarityRouter(personality["examples"])


# ---------------- INTENT DETECTION ----------------
def detect_tool(user_input: str) -> str | None:
    text = user_input.lower()

    for tool_name, keywords in personality["tool_rules"].items():
        if any(keyword in text for keyword in keywords):
            return tool_name

    return None


def pick_random(key: str) -> str:
    return random.choice(personality[key])


def get_name() -> str:
    return random.choice(personality["names"])


# ---------------- CHAT LOOP ----------------
def chat_with_bot():
    print("🤖 Yo Buddy! Smart tool-based assistant is live 😎")
    print("Ask me about Python, stocks, gold/silver, or research papers.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("🤖 Later Chad, take care 🔥")
            break

        name = get_name()
        greeting = pick_random("greetings").format(name=name)
        filler = pick_random("fillers")
        signoff = pick_random("sign_offs").format(name=name)

        print(f"\n🤖 {greeting}")
        print(f"{filler}")

        tool = router.route(user_input)

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

        # ---------------- OUTPUT ----------------
        max_len = personality.get("max_context_chars", 1200)
        print(result[:max_len])

        print(f"\n{signoff}\n")


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    chat_with_bot()
