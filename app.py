import os
import io
import csv
import html
import hashlib
import datetime
import requests
import streamlit as st
from order_parser import parse_order

STT_URL = "https://api.vachana.ai/stt/v3"
TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

# Timbre v3.0 voices (each one speaks all 10 languages)
VOICES = ["Shivani", "Avinash", "Lakshmi", "Kalpana", "Shubham", "Prakash",
          "Devansh", "Yashraj", "Chetana", "Vasudha", "Riyaa", "Tarika", "Harshad"]

# label -> STT settings + which phrase set Timbre uses to speak the bill
LANGUAGES = {
    "Hindi (हिन्दी)":     {"code": "hi-IN", "model": None, "format": None, "group": "hi",
                           "hint": "2 किलो चावल और एक अमूल बटर देना"},
    "Hinglish":           {"code": "hi-IN", "model": "prisma-v3.0", "format": "transliterate", "group": "hi",
                           "hint": "do kilo chawal aur ek Amul butter dena"},
    "Malayalam (മലയാളം)": {"code": "ml-IN", "model": None, "format": None, "group": "ml",
                           "hint": "രണ്ട് കിലോ അരിയും ഒരു ലിറ്റർ എണ്ണയും"},
    "Manglish":           {"code": "ml-IN", "model": "prisma-v3.0", "format": "transliterate", "group": "ml",
                           "hint": "randu kilo ari, oru litre enna"},
    "Tamil (தமிழ்)":      {"code": "ta-IN", "model": None, "format": None, "group": "ta",
                           "hint": "இரண்டு கிலோ அரிசி ஒரு லிட்டர் எண்ணெய்"},
}

PHRASES = {
    "hi": {"intro": "आपका बिल तैयार है।", "total": "कुल", "rupees": "रुपये"},
    "ml": {"intro": "നിങ്ങളുടെ ബിൽ തയ്യാറാണ്.", "total": "ആകെ", "rupees": "രൂപ"},
    "ta": {"intro": "உங்கள் பில் தயார்.", "total": "மொத்தம்", "rupees": "ரூபாய்"},
}

UNIT_SPOKEN = {"kg": "kilo", "litre": "litre", "packet": "packet", "piece": "piece"}

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def int_words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return ONES[n // 100] + " hundred" + (" " + int_words(n % 100) if n % 100 else "")
    if n < 100000:
        return int_words(n // 1000) + " thousand" + (" " + int_words(n % 1000) if n % 1000 else "")
    return str(n)


def qty_words(q):
    if q == int(q):
        return int_words(int(q))
    whole = int(q)
    if q - whole == 0.5:
        return "half" if whole == 0 else int_words(whole) + " and a half"
    return str(q)


def spoken_bill(items, total, group):
    """Numbers are written as words, as Gnani's docs recommend for TTS."""
    p = PHRASES[group]
    parts = [p["intro"]]
    for i in items:
        unit = UNIT_SPOKEN.get(i["Unit"], i["Unit"])
        parts.append(f"{i['Item']}, {qty_words(i['Qty'])} {unit}.")
    parts.append(f"{p['total']} {int_words(int(round(total)))} {p['rupees']}.")
    return " ".join(parts)


def bill_csv(items, total):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Item", "Qty", "Unit", "Rate (Rs)", "Amount (Rs)"])
    for i in items:
        w.writerow([i["Item"], i["Qty"], i["Unit"], i["Rate (Rs)"], i["Amount (Rs)"]])
    w.writerow(["", "", "", "TOTAL", total])
    return buf.getvalue().encode("utf-8-sig")  # utf-8-sig so Excel shows it correctly


def bill_html(items, total, transcript):
    now = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    rows = "".join(
        f"<tr><td>{html.escape(str(i['Item']))}</td><td>{i['Qty']} {html.escape(i['Unit'])}</td>"
        f"<td class='r'>{i['Rate (Rs)']}</td><td class='r'>{i['Amount (Rs)']:.2f}</td></tr>"
        for i in items
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Bill</title>
<style>
body{{font-family:Arial,'Noto Sans',sans-serif;max-width:560px;margin:30px auto;padding:0 16px;color:#222}}
h1{{margin:0}} .sub{{color:#777;font-size:13px;margin-bottom:18px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:8px;border-bottom:1px solid #ddd;text-align:left}}
.r{{text-align:right}} .total td{{font-weight:bold;font-size:18px;border-top:2px solid #222}}
.said{{margin-top:18px;font-size:13px;color:#555}}
</style></head><body>
<h1>🛒 Padosi Bill</h1>
<div class="sub">{now}</div>
<table>
<tr><th>Item</th><th>Qty</th><th class="r">Rate (Rs)</th><th class="r">Amount (Rs)</th></tr>
{rows}
<tr class="total"><td colspan="3">Total</td><td class="r">Rs {total:,.2f}</td></tr>
</table>
<div class="said">Order heard: {html.escape(transcript)}</div>
<div class="said">Made with Gnani Prisma (speech to text) and Gnani Timbre (text to speech).</div>
</body></html>""".encode("utf-8")


st.set_page_config(page_title="Padosi Voice Order Taker", page_icon="🛒")
st.title("🛒 Padosi Voice Order Taker")
st.caption("Speak your order in your language. Gnani Prisma listens, Gnani Timbre reads the bill back.")

api_key = st.sidebar.text_input("Gnani API key", type="password",
                                value=os.getenv("GNANI_API_KEY", ""))
voice = st.sidebar.selectbox("Timbre voice", VOICES)

lang_label = st.selectbox("Language", list(LANGUAGES.keys()))
cfg = LANGUAGES[lang_label]
st.info(f"Try saying: {cfg['hint']}")

audio = st.audio_input("Tap to record your order", key=f"mic_{lang_label}")

if audio and api_key:
    audio_bytes = audio.getvalue()
    sig = hashlib.md5(audio_bytes + lang_label.encode()).hexdigest()

    # Only call Gnani STT for a NEW recording (button clicks re-run this script)
    if st.session_state.get("stt_sig") != sig:
        data = {"language_code": cfg["code"]}
        if cfg["model"]:
            data["model"] = cfg["model"]
        if cfg["format"]:
            data["format"] = cfg["format"]
        with st.spinner("Transcribing..."):
            r = requests.post(
                STT_URL,
                headers={"X-API-Key-ID": api_key},
                files={"audio_file": ("order.wav", audio_bytes, "audio/wav")},
                data=data,
                timeout=60,
            )
        st.session_state["stt_sig"] = sig
        st.session_state.pop("tts_audio", None)
        if r.status_code != 200:
            st.session_state["stt_error"] = f"Gnani API error {r.status_code}: {r.text}"
            st.session_state["stt_body"] = None
        else:
            st.session_state["stt_error"] = None
            st.session_state["stt_body"] = r.json()

    if st.session_state.get("stt_error"):
        st.error(st.session_state["stt_error"])
    else:
        body = st.session_state["stt_body"]
        transcript = body.get("transcript", "")
        st.subheader("You said")
        st.write(transcript if transcript else "(no speech detected)")

        items, unknown = parse_order(transcript)
        if items:
            total = sum(i["Amount (Rs)"] for i in items)
            st.subheader("Your bill")
            st.table(items)
            st.metric("Total", f"Rs {total:,.2f}")

            # ---- Timbre: read the bill aloud ----
            if st.button("🔊 Read bill aloud"):
                spoken = spoken_bill(items, total, cfg["group"])
                with st.spinner("Timbre is speaking..."):
                    tr = requests.post(
                        TTS_URL,
                        headers={"Content-Type": "application/json",
                                 "X-API-Key-ID": api_key},
                        json={
                            "text": spoken,
                            "voice": voice,
                            "model": "timbre-v3.0",
                            "language": "auto",
                            "speed": 1.0,
                            "audio_config": {"sample_rate": 24000, "num_channels": 1,
                                             "sample_width": 2, "encoding": "linear_pcm",
                                             "container": "wav"},
                        },
                        timeout=60,
                    )
                if tr.status_code == 200:
                    st.session_state["tts_audio"] = tr.content
                    st.session_state["tts_text"] = spoken
                else:
                    st.error(f"Timbre error {tr.status_code}: {tr.text}")

            if st.session_state.get("tts_audio"):
                st.audio(st.session_state["tts_audio"], format="audio/wav")
                with st.expander("What was spoken"):
                    st.write(st.session_state["tts_text"])

            # ---- Downloads ----
            st.subheader("Download")
            c1, c2, c3 = st.columns(3)
            c1.download_button("📄 Bill (HTML / print as PDF)",
                               bill_html(items, total, transcript),
                               file_name="bill.html", mime="text/html")
            c2.download_button("📊 Bill (CSV)", bill_csv(items, total),
                               file_name="bill.csv", mime="text/csv")
            if st.session_state.get("tts_audio"):
                c3.download_button("🔊 Spoken bill (WAV)", st.session_state["tts_audio"],
                                   file_name="bill_audio.wav", mime="audio/wav")
        elif transcript:
            st.warning("I heard you, but found no items from the catalog.")
        for u in unknown:
            st.warning(f"Couldn't find this item in the catalog: {u}")

        with st.expander("Debug: raw API response"):
            st.json(body)
elif audio and not api_key:
    st.info("Paste your Gnani API key in the sidebar first.")