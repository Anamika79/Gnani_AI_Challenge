import re
import difflib

# item: (price in Rs, unit, aliases in Hindi / Hinglish / Malayalam / Manglish / Tamil)
# Native-script aliases are STEMS (they match inflected forms like അരിയും).
CATALOG = {
    "Rice": (60, "kg", [
        "चावल", "chawal", "chaval", "chaaval", "rice",
        "അരി", "ariyum", "ari", "அரிசி", "arisi"]),
    "Atta": (45, "kg", [
        "आटा", "आटे", "atta", "aata",
        "ആട്ട", "ഗോതമ്പ", "gothambu", "ஆட்டா", "கோதுமை"]),
    "Dal": (120, "kg", [
        "दाल", "dal", "daal",
        "ദാൽ", "പരിപ്പ", "parippu", "பருப்ப", "paruppu"]),
    "Sugar": (45, "kg", [
        "चीनी", "शक्कर", "cheeni", "shakkar", "sugar",
        "പഞ്ചസാര", "panchasara", "சர்க்கரை", "sakkarai"]),
    "Amul Butter": (58, "packet", [
        "बटर", "butter", "ബട്ടർ", "വെണ്ണ", "venna", "வெண்ணெய", "பட்டர்"]),
    "Milk": (30, "packet", [
        "दूध", "doodh", "dudh", "milk",
        "പാൽ", "പാല", "paal", "pal", "பால"]),
    "Eggs": (7, "piece", [
        "अंडे", "अंडा", "ande", "anda", "egg", "eggs",
        "മുട്ട", "mutta", "முட்ட", "muttai"]),
    "Cooking Oil": (150, "litre", [
        "तेल", "तिल", "tel", "til", "oil",
        "എണ്ണ", "enna", "எண்ணெய", "ennai"]),
    "Salt": (20, "packet", [
        "नमक", "namak", "salt", "ഉപ്പ", "uppu", "உப்ப"]),
    "Tea": (90, "packet", [
        "चायपत्ती", "चाय", "chai", "tea",
        "ചായപ്പൊടി", "ചായ", "chayapodi", "தேயிலை", "டீ"]),
}

NUMBER_WORDS = {
    # Hindi / Hinglish
    "ek": 1, "एक": 1, "do": 2, "दो": 2, "teen": 3, "तीन": 3,
    "char": 4, "chaar": 4, "चार": 4, "paanch": 5, "panch": 5, "पांच": 5, "पाँच": 5,
    "chhe": 6, "छह": 6, "saat": 7, "सात": 7, "aath": 8, "आठ": 8,
    "nau": 9, "नौ": 9, "das": 10, "दस": 10,
    "aadha": 0.5, "adha": 0.5, "आधा": 0.5, "half": 0.5,
    "dedh": 1.5, "डेढ़": 1.5, "dhai": 2.5, "ढाई": 2.5,
    # Malayalam
    "ഒരു": 1, "ഒന്ന്": 1, "ഒന്നു": 1, "രണ്ട്": 2, "രണ്ടു": 2,
    "മൂന്ന്": 3, "മൂന്നു": 3, "നാല്": 4, "നാലു": 4, "അഞ്ച്": 5, "അഞ്ചു": 5,
    "ആറ്": 6, "ആറു": 6, "ഏഴ്": 7, "ഏഴു": 7, "എട്ട്": 8, "എട്ടു": 8,
    "ഒമ്പത്": 9, "ഒൻപത്": 9, "പത്ത്": 10, "പത്തു": 10,
    "അര": 0.5, "അരക്കിലോ": 0.5, "അരകിലോ": 0.5, "ഒന്നര": 1.5, "രണ്ടര": 2.5,
    # Manglish
    "oru": 1, "onnu": 1, "randu": 2, "rendu": 2, "moonnu": 3, "munnu": 3,
    "naalu": 4, "anchu": 5, "aaru": 6, "ezhu": 7, "ettu": 8, "ombathu": 9,
    "pathu": 10, "ara": 0.5, "onnara": 1.5, "randara": 2.5,
    # Tamil
    "ஒரு": 1, "ஒன்று": 1, "இரண்டு": 2, "ரெண்டு": 2, "மூன்று": 3,
    "நான்கு": 4, "ஐந்து": 5, "ஆறு": 6, "ஏழு": 7, "எட்டு": 8,
    "ஒன்பது": 9, "பத்து": 10, "அரை": 0.5, "ஒன்றரை": 1.5, "இரண்டரை": 2.5,
}

DOZEN_WORDS = ["दर्जन", "डज़न", "डजन", "dozen", "darjan", "dazan",
               "ഡസൻ", "ഡസന്‍", "டஜன்", "டசன்"]

# ---- lookup tables built once ----
LATIN_ALIASES = {}   # latin alias -> item
STEM_ALIASES = []    # (native-script stem, item)
for _name, (_p, _u, _aliases) in CATALOG.items():
    for _a in _aliases:
        _a = _a.lower()
        if _a.isascii():
            LATIN_ALIASES[_a] = _name
        else:
            STEM_ALIASES.append((_a, _name))
STEM_ALIASES.sort(key=lambda x: -len(x[0]))


def find_item(tok):
    # 1. Native script (Hindi / Malayalam / Tamil): match word stems
    if not tok.isascii():
        for stem, name in STEM_ALIASES:
            if tok.startswith(stem):
                return name
        return None
    # 2. Latin script (Hinglish / Manglish): exact, prefix, then fuzzy
    if tok in LATIN_ALIASES:
        return LATIN_ALIASES[tok]
    if len(tok) >= 4:
        for alias, name in LATIN_ALIASES.items():
            if len(alias) >= 4 and tok.startswith(alias):
                return name
        close = difflib.get_close_matches(tok, LATIN_ALIASES.keys(), n=1, cutoff=0.8)
        if close:
            return LATIN_ALIASES[close[0]]
    return None


def clean_tokens(text):
    text = text.replace("चाय पत्ती", "चायपत्ती")
    tokens = []
    for t in text.split():
        t = t.strip(",।.!?").lower()
        if t:
            tokens.append(t)
    return tokens


def quantity_from(tokens):
    """Pick the number closest to the item word (searching backwards)."""
    for tok in reversed(tokens):
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            return float(tok), True
        if tok in NUMBER_WORDS:
            return float(NUMBER_WORDS[tok]), True
    return 1.0, False  # no number said, assume 1


def parse_order(text):
    """Returns (items, unknown_parts). Works for all supported languages."""
    tokens = clean_tokens(text)
    items, pending = [], []

    for tok in tokens:
        name = find_item(tok)
        if name:
            price, unit, _ = CATALOG[name]
            qty, _ = quantity_from(pending)
            if unit == "piece" and any(d in pending for d in DOZEN_WORDS):
                qty *= 12
            qty = int(qty) if qty == int(qty) else qty
            items.append({"Item": name, "Qty": qty, "Unit": unit,
                          "Rate (Rs)": price,
                          "Amount (Rs)": round(qty * price, 2)})
            pending = []
        else:
            pending.append(tok)

    unknown = []
    if pending:
        _, has_number = quantity_from(pending)
        if has_number:
            unknown.append(" ".join(pending))
    return items, unknown


if __name__ == "__main__":
    tests = [
        "2 किलो आटा एक किलो तिल 2 डज़न अंडा",                # Hindi
        "do kilo chawal aur ek Amul butter dena",             # Hinglish
        "രണ്ട് കിലോ അരിയും ഒരു ലിറ്റർ എണ്ണയും ഒരു ഡസൻ മുട്ടയും",  # Malayalam
        "randu kilo ari, oru litre enna, onnara dozen mutta", # Manglish
        "இரண்டு கிலோ அரிசி ஒரு லிட்டர் எண்ணெய் ஒரு டஜன் முட்டை",  # Tamil
    ]
    for t in tests:
        print(t, "->", parse_order(t))