"""MediBot - a small conversational symptom checker.

Flow (matches the methodology diagram in the project report):
  start -> user describes symptoms -> bot extracts them -> asks follow-up
  questions chosen by the model -> predicts disease with confidence ->
  offers doctor information (Y/N).
"""
import re

from . import symptom_model as sm
from .knowledge import DISEASES, EMERGENCY_NUMBERS, RED_FLAGS, SYMPTOMS

NEG = r"(?:no|not|without|don'?t have|do not have|never|dont have)\s+(?:\w+\s+){0,2}"
YES = {"yes", "y", "yeah", "yep", "yup", "sure", "ok", "okay", "i do", "true", "have"}
NO = {"no", "n", "nope", "nah", "not really", "don't", "dont", "false"}
RESET = {"reset", "restart", "start over", "new", "clear"}


def extract(text):
    """Return (present, absent) symptom key sets found in free text."""
    t = " " + text.lower() + " "
    present, absent = set(), set()
    # longest synonyms first so "high fever" wins over "fever"
    pairs = sorted(((syn, key) for key, (_, syns) in SYMPTOMS.items() for syn in syns), key=lambda p: -len(p[0]))
    consumed = t
    for syn, key in pairs:
        pat = r"\b" + re.escape(syn) + r"\b"
        if not re.search(pat, consumed):
            continue
        if re.search(NEG + re.escape(syn), consumed):
            absent.add(key)
        else:
            present.add(key)
        consumed = re.sub(pat, " ", consumed)
    if "high_fever" in present:
        present.add("fever")
    return present, absent - present


def _fmt(keys):
    return ", ".join(SYMPTOMS[k][0].lower() for k in keys)


def _new_state():
    return {"present": [], "absent": [], "asked": [], "pending": None, "stage": "collect", "result": None}


def start():
    return _new_state(), [
        "Hi! I'm **MediBot** 🩺, your AI health assistant.",
        "Tell me what you're feeling - for example: *\"I have fever, headache and body pain\"*.",
    ]


def _final(state):
    present, absent = set(state["present"]), set(state["absent"])
    ranked = sm.predict(present, absent)[:3]
    top, p = ranked[0]
    info = DISEASES[top]
    conf = round(min(p, 0.97) * 100, 1)
    state["stage"] = "doctor"
    state["result"] = {"disease": top, "confidence": conf, "specialist": info["specialist"]}
    lines = [
        f"Based on what you told me ({_fmt(present)}), the most likely condition is **{top}** "
        f"with about **{conf}% confidence**.",
        info["desc"],
    ]
    others = [f"{d} ({round(min(pp, .97) * 100, 1)}%)" for d, pp in ranked[1:] if pp > 0.03]
    if others:
        lines.append("Other possibilities: " + ", ".join(others) + ".")
    lines.append("**What you can do:**\n" + "\n".join("• " + x for x in info["precautions"]))
    for combo, msg in RED_FLAGS:
        if combo <= present:
            lines.append(f"⚠️ **Warning:** {msg} Seek medical care immediately. {EMERGENCY_NUMBERS}")
            break
    lines.append("Would you like **doctor info** (which specialist to see)? Reply **Y** or **N**.")
    return lines, {"type": "result", "disease": top, "confidence": conf, "severity": info["severity"]}


def reply(state, text):
    """Advance the conversation. Returns (state, bot_messages, meta)."""
    text = (text or "").strip()
    low = text.lower()
    if low in RESET:
        s, msgs = start()
        return s, msgs, {"type": "reset"}

    # -- doctor info stage ---------------------------------------------------
    if state["stage"] == "doctor":
        if low in YES or low.startswith("y"):
            r = state["result"]
            return state, [
                f"For **{r['disease']}**, consider seeing a **{r['specialist']}**.",
                "Take along any test reports, and note when the symptoms started. "
                "This chatbot is not a diagnosis - please confirm with a qualified doctor.",
                "Type *reset* to check new symptoms.",
            ], {"type": "doctor"}
        if low in NO or low.startswith("n"):
            return state, ["Okay! Take care and get well soon. 💙 Type *reset* to start again."], {"type": "end"}
        return state, ["Please reply **Y** for doctor info or **N** to finish."], {}

    present, absent = set(state["present"]), set(state["absent"])
    asked = list(state["asked"])

    # -- answering a follow-up question -------------------------------------
    if state["pending"]:
        key = state["pending"]
        if low in YES or low.startswith("yes"):
            present.add(key)
        elif low in NO or low.startswith("no"):
            absent.add(key)
        else:
            p2, a2 = extract(text)
            present |= p2
            absent |= a2
        state["pending"] = None
    else:
        p2, a2 = extract(text)
        if not p2 and not a2:
            return state, [
                "I couldn't pick out a symptom there. Try simple words like *fever, cough, headache, "
                "vomiting, rash, chest pain*."
            ], {}
        present |= p2
        absent |= a2
        present -= absent

    state["present"], state["absent"] = sorted(present), sorted(absent)

    if not present:
        return state, ["Thanks. Please tell me at least one symptom you **do** have."], {}

    ranked = sm.predict(present, absent)
    top_p = ranked[0][1]
    nxt = sm.next_question(present, absent, set(asked))
    if (top_p >= 0.75 and len(present) >= 2) or nxt is None or len(asked) >= 5:
        lines, meta = _final(state)
        return state, lines, meta

    asked.append(nxt)
    state["asked"] = asked
    state["pending"] = nxt
    label = SYMPTOMS[nxt][0].lower()
    return state, [f"Got it ({_fmt(present)}). Do you also have **{label}**? (yes / no)"], {"type": "question", "symptom": nxt}
