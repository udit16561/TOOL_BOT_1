from langchain.tools import tool
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
import yfinance as yf
from scholarly import scholarly
import requests
import re

# ------------------------------------------------------------------
# TOOL 1: Python Documentation Retrieval
# ------------------------------------------------------------------



@tool
def get_currency_rate(query: str) -> str:
    """
    Convert currency amounts using live Yahoo Finance FX rates.

    Supports examples like:
    - '1633 dollar to inr'
    - '250 usd to eur'
    - '1000 yen to usd'
    - 'gbp to inr'
    - 'aud to cad'
    """

    text = query.lower()

    # ---------------- AMOUNT EXTRACTION ----------------
    amount_match = re.search(r"(\d+(\.\d+)?)", text)
    amount = float(amount_match.group(1)) if amount_match else 1.0

    # ---------------- CURRENCY ALIASES ----------------
    currency_aliases = {
        # Americas
        "usd": "USD", "dollar": "USD", "dollars": "USD",
        "cad": "CAD", "canadian dollar": "CAD",

        # Europe
        "eur": "EUR", "euro": "EUR", "euros": "EUR",
        "gbp": "GBP", "pound": "GBP", "pounds": "GBP",

        # Asia
        "inr": "INR", "rupee": "INR", "rupees": "INR", "rs": "INR",
        "jpy": "JPY", "yen": "JPY",
        "cny": "CNY", "yuan": "CNY",
        "krw": "KRW", "won": "KRW",

        # Middle East
        "aed": "AED", "dirham": "AED",
        "sar": "SAR", "riyal": "SAR",

        # Oceania
        "aud": "AUD", "australian dollar": "AUD",
        "nzd": "NZD", "new zealand dollar": "NZD",

        # Europe (others)
        "chf": "CHF", "swiss franc": "CHF",
        "sek": "SEK", "swedish krona": "SEK",
        "nok": "NOK", "norwegian krone": "NOK"
    }

    # ---------------- DETECT CURRENCIES ----------------
    detected = []
    for alias, code in currency_aliases.items():
        if alias in text:
            detected.append(code)

    # Remove duplicates while preserving order
    currencies = list(dict.fromkeys(detected))

    if len(currencies) == 1:
        base = currencies[0]
        target = "USD" if base != "USD" else "INR"
    elif len(currencies) >= 2:
        base, target = currencies[0], currencies[1]
    else:
        return (
            "Buddy 😄 I couldn’t figure out the currencies.\n"
            "Try examples like:\n"
            "- 1633 dollar to inr\n"
            "- 250 usd to eur\n"
            "- 1000 yen to usd\n"
            "- gbp to inr"
        )

    # ---------------- FETCH FX RATE ----------------
    symbol = f"{base}{target}=X"
    data = yf.Ticker(symbol).history(period="1d")

    if data.empty:
        return f"Damn Buddy, I couldn’t fetch exchange rate for {base} → {target}."

    rate = float(data["Close"].iloc[-1])
    converted = round(amount * rate, 2)

    # ---------------- RESPONSE ----------------
    if amount == 1.0:
        return f"Current rate: 1 {base} ≈ {round(rate,4)} {target}"

    return (
        f"{amount} {base} ≈ {converted} {target}\n"
        f"(Rate: 1 {base} = {round(rate,4)} {target})"
    )


# ------------------------------------------------------------------
# TOOL 2: Market Prices (Gold / Silver / Indices) with Currency
# ------------------------------------------------------------------


@tool
def get_market_price(query: str) -> str:
    """
    Fetch Gold or Silver price for ANY weight in grams.
    Supports INR and USD.

    Examples:
    - gold price for 150 gm in inr
    - silver price for 1000 grams
    - gold price per gram
    """

    query = query.lower()

    # ---------------- METAL DETECTION ----------------
    symbols = {
        "gold": "GC=F",    # USD per troy ounce
        "silver": "SI=F"   # USD per troy ounce
    }

    metal = None
    for m in symbols:
        if m in query:
            metal = m
            break

    if not metal:
        return (
            "Buddy 😅 I couldn’t detect the metal.\n"
            "Try:\n"
            "- gold price for 150 gm\n"
            "- silver price for 1000 grams"
        )

    # ---------------- WEIGHT EXTRACTION ----------------
    # Default: 1 gram
    weight_grams = 1.0

    weight_match = re.search(r"(\d+(\.\d+)?)\s*(gm|gram|grams|g)", query)
    if weight_match:
        weight_grams = float(weight_match.group(1))

    # ---------------- CURRENCY ----------------
    currency = "usd"
    if "inr" in query or "rupee" in query or "rs" in query:
        currency = "inr"

    # ---------------- FETCH PRICE ----------------
    data = yf.Ticker(symbols[metal]).history(period="1d")
    if data.empty:
        return f"Damn Buddy, I couldn’t fetch {metal} price right now."

    price_per_ounce_usd = float(data["Close"].iloc[-1])

    # ---------------- UNIT CONVERSION ----------------
    # 1 troy ounce = 31.1035 grams
    price_per_gram_usd = price_per_ounce_usd / 31.1035
    total_price_usd = price_per_gram_usd * weight_grams

    # ---------------- CURRENCY CONVERSION ----------------
    if currency == "inr":
        rate = _get_fx_rate("USD", "INR")
        if rate == 0.0:
            return "Damn Buddy, I couldn’t fetch USD → INR rate."

        total_price = round(total_price_usd * rate, 2)
        return (
            f"Current {metal.upper()} price is approx ₹{total_price} INR "
            f"for {weight_grams:g} grams"
        )

    total_price = round(total_price_usd, 2)
    return (
        f"Current {metal.upper()} price is approx ${total_price} USD "
        f"for {weight_grams:g} grams"
    )

# ------------------------------------------------------------------
# TOOL 3: Currency Converter (Live)
# ------------------------------------------------------------------
@tool
def get_currency_rate(query: str) -> str:
    """
    Convert any currency into INR (or between any two currencies).

    Examples:
    - '100 eur to inr'
    - '500 gbp to inr'
    - '1000 jpy to inr'
    - 'usd to inr'
    """

    import re

    text = query.lower()

    # ---------------- AMOUNT ----------------
    match = re.search(r"(\d+(\.\d+)?)", text)
    amount = float(match.group(1)) if match else 1.0

    # ---------------- CURRENCY ALIASES ----------------
    aliases = {
        "usd": "USD", "dollar": "USD",
        "eur": "EUR", "euro": "EUR",
        "gbp": "GBP", "pound": "GBP",
        "inr": "INR", "rupee": "INR",
        "jpy": "JPY", "yen": "JPY",
        "aud": "AUD",
        "cad": "CAD",
        "chf": "CHF",
        "cny": "CNY",
        "sar": "SAR",
        "aed": "AED"
    }

    found = []
    for word, code in aliases.items():
        if word in text:
            found.append(code)

    found = list(dict.fromkeys(found))  # remove duplicates

    # ---------------- BASE / TARGET ----------------
    if len(found) == 1:
        base = found[0]
        target = "INR"
    elif len(found) >= 2:
        base, target = found[0], found[1]
    else:
        return (
            "Buddy 😄 I couldn’t detect the currencies.\n"
            "Try: '100 eur to inr' or '500 gbp to inr'"
        )

    # ---------------- FX RATE ----------------
    rate = _get_fx_rate(base, target)

    if rate == 0.0:
        return f"Damn Buddy, I couldn’t fetch {base} → {target} rate."

    converted = round(amount * rate, 2)

    if amount == 1.0:
        return f"1 {base} ≈ {round(rate,4)} {target}"

    return (
        f"{amount} {base} ≈ {converted} {target}\n"
        f"(Rate: 1 {base} = {round(rate,4)} {target})"
    )
    

def _get_fx_rate(base: str, target: str) -> float:
    """
    Internal helper: returns numeric FX rate using Yahoo Finance.
    If base == target, returns 1.0
    """
    if base == target:
        return 1.0

    symbol = f"{base}{target}=X"
    data = yf.Ticker(symbol).history(period="1d")

    if data.empty:
        return 0.0

    return float(data["Close"].iloc[-1])


# ------------------------------------------------------------------
# TOOL 4: Google Scholar – Best Paper by Citations
# ------------------------------------------------------------------

@tool
def search_research_papers(query: str) -> str:
    """
    Search research papers using Semantic Scholar API
    ranked by citation count.
    """

    text = query.lower()

    # extract "top N"
    match = re.search(r"top\s*(\d+)", text)
    top_n = int(match.group(1)) if match else 1
    top_n = min(top_n, 10)

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": 20,
        "fields": "title,authors,year,venue,citationCount,abstract"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return "Buddy 😓 Paper server is busy. Try again in a moment."

    data = response.json()
    papers = data.get("data", [])

    if not papers:
        return "Sorry Buddy, I couldn’t find relevant papers."

    # sort by citations
    papers = sorted(papers, key=lambda x: x.get("citationCount", 0), reverse=True)

    result = []

    for i, p in enumerate(papers[:top_n], start=1):
        authors = ", ".join([a["name"] for a in p.get("authors", [])][:4])

        result.append(
            f"#{i}\n"
            f"Title: {p.get('title','N/A')}\n"
            f"Authors: {authors}\n"
            f"Year: {p.get('year','N/A')}\n"
            f"Venue: {p.get('venue','N/A')}\n"
            f"Citations: {p.get('citationCount',0)}"
        )

    return "\n\n---\n\n".join(result)
@tool
def describe_research_paper(query: str) -> str:
    """
    Describe a research paper with abstract and inferred conclusion.
    """


    search = scholarly.search_pubs(query)

    try:
        paper = next(search)
    except StopIteration:
        return (
            "Buddy 😅 I couldn’t clearly identify the paper.\n"
            "Try copying the paper title or ask:\n"
            "- describe paper <title>\n"
            "- explain research on <topic>"
        )

    bib = paper.get("bib", {})
    title = bib.get("title", "N/A")
    abstract = bib.get("abstract")

    response = [
        f"📄 Title: {title}",
        f"👥 Authors: {bib.get('author','N/A')}",
        f"📅 Year: {bib.get('year','N/A')}",
        f"🏛 Venue: {bib.get('venue','N/A')}"
    ]

    response.append("\n🧠 Abstract:")
    response.append(abstract if abstract else "Abstract not publicly available.")

    response.append("\n✅ Likely Conclusion:")
    response.append(
        "The paper concludes by demonstrating the effectiveness of the proposed "
        "approach over existing methods, while outlining limitations and future work."
    )

    response.append(
        "\n⚠️ Note: Conclusion is inferred using academic heuristics."
    )

    return "\n".join(response)