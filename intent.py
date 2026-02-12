import json

with open("personality.json", "r") as f:
    personality = json.load(f)


def detect_tool(user_input: str) -> str | None:
    text = user_input.lower()

    for tool, keywords in personality["tool_rules"].items():
        if any(k in text for k in keywords):
            return tool

    return None
