# 🛒 Kirana Voice Order Taker

**Speak your order. Get the bill. Hear it read back. In five Indian languages.**

A small web app for neighbourhood kirana stores. A shopkeeper or customer speaks an order such as *"do kilo chawal aur ek Amul butter dena"*. The app transcribes it, turns it into an itemised bill, reads the bill back aloud, and lets you download it.

Built for the **Great Indian AI Internship Challenge** by Gnani AI.
`#GnaniAI` `#GreatIndianAIInternshipChallenge`

🔗 **Live app:** https://gnaniaichallenge-rg7enpxuhoyec5sgpvsbot.streamlit.app/

---

## The problem

Many kirana orders are still given by voice, in the language the customer is comfortable with, often mixing languages mid-sentence. Orders are noted by hand or remembered, which leads to mistakes, slow billing and no written record. Most billing tools expect typing and English item names.

## The solution

Speak the order in your own language and get a bill in seconds, with a spoken read-back so both sides can confirm it.

## Features

- 🎙️ **Voice ordering** - record directly in the browser.
- 🌐 **Five languages** - Hindi, Hinglish, Malayalam, Manglish and Tamil, chosen from a dropdown.
- 🧾 **Instant itemised bill** - items, quantities, rates and total.
- 🔊 **Read bill aloud** - Gnani Timbre speaks the bill, with a choice of voices.
- ⬇️ **Downloads** - printable bill (HTML, save as PDF from the browser), CSV for Excel, and the spoken bill as WAV audio.
- 🔍 **Debug view** - shows the raw Gnani API response, which helps when tuning item names.

## Gnani AI models used

| Model | Used for |
|---|---|
| **Prisma v2.5** (speech to text) | Transcription in native script for Hindi, Malayalam and Tamil |
| **Prisma v3.0** (speech to text) | Hinglish and Manglish, using the `transliterate` format so the transcript is written in Latin letters |
| **Timbre v3.0** (text to speech) | Reading the final bill aloud; the voice is selectable |

## How it works

```
 Browser mic
     │  audio
     ▼
 Gnani Prisma (STT)  ──►  transcript
                              │
                              ▼
                     order_parser.py
          (finds items + quantities, prices the order)
                              │
                              ▼
                  Bill table + total on screen
                    │                   │
                    ▼                   ▼
          Gnani Timbre (TTS)     Download HTML / CSV
          reads the bill aloud
```

1. **Record** - Streamlit's built-in audio recorder captures the order.
2. **Transcribe** - the audio is sent to `POST https://api.vachana.ai/stt/v3` with the chosen `language_code` (`hi-IN`, `ml-IN`, `ta-IN`). Hinglish and Manglish also send `model=prisma-v3.0` and `format=transliterate`.
3. **Parse** - `order_parser.py` scans the transcript word by word. Each time it finds an item word, it takes the nearest quantity before it (digits or spoken numbers such as *do*, *ek*, *randu*, *ஒரு*, *ഒരു*). Words like *dozen* and *half* are handled.
4. **Bill** - items are priced from a built-in catalog and totalled.
5. **Speak** - a short summary, with numbers written as words as Gnani's TTS guide recommends, is sent to `POST https://api.vachana.ai/api/v1/tts/inference` using `timbre-v3.0`.

### Parser details

- **Stem matching for Malayalam and Tamil** - these languages add endings to words (for example *ariyum* means "and rice"), so native-script aliases are matched as word stems.
- **Fuzzy matching for Latin script** - Hinglish and Manglish spellings vary, so Latin tokens are matched by exact match, prefix, then fuzzy similarity.
- **Unknown items are flagged, never guessed.**

## Project structure

```
.
├── app.py            # Streamlit UI, Gnani STT and TTS calls, downloads
├── order_parser.py   # Item, quantity and price extraction (multilingual)
├── requirements.txt  # streamlit, requests
└── README.md
```

## Run it locally

Requires Python 3.10 or newer and a Gnani API key from [app.gnani.ai/voice](https://app.gnani.ai/voice).

```bash
pip install -r requirements.txt
streamlit run app.py
```

Provide your key in the sidebar, or set it as an environment variable before starting:

```bash
export GNANI_API_KEY="your-api-key"      # Windows PowerShell: $env:GNANI_API_KEY="your-api-key"
```

`requirements.txt`:

```
streamlit
requests
```

To test the parser on its own, without the web app or any API calls:

```bash
python order_parser.py
```

## Try it

Pick a language, tap the recorder and say one of these:

| Language | Example |
|---|---|
| Hindi | 2 किलो चावल और एक अमूल बटर देना |
| Hinglish | do kilo chawal aur ek Amul butter dena |
| Malayalam | രണ്ട് കിലോ അരിയും ഒരു ലിറ്റർ എണ്ണയും |
| Manglish | randu kilo ari, oru litre enna |
| Tamil | இரண்டு கிலோ அரிசி ஒரு லிட்டர் எண்ணெய் |

Then press **🔊 Read bill aloud** and try the download buttons.

## Security note

The API key is entered in the app sidebar or read from the `GNANI_API_KEY` environment variable. It is never written into the code or committed to the repository.

## Known limitations

- The catalog is a demo list of 10 common items with sample prices, not a real inventory.
- The parser is rule-based, so unusual phrasing or unlisted items may not be recognised. Unmatched items are shown as warnings.
- Speech recognition can mishear words (for example *tel* heard as *til*), so some common mis-hearings are added as aliases.
- In the spoken bill, item names and amounts are spoken as English words, while the intro and "total" are in the chosen language.
- Gnani's API allows one active request at a time per account, so rapid repeated recordings may need a short wait.

## Roadmap

- Shop-owned catalogs and live prices
- An LLM-based parser for free-form orders and unlisted items
- More languages (Telugu, Kannada, Marathi, Bengali and others that Prisma and Timbre already support)
- Spoken bills with numbers in native-language words
- WhatsApp or phone-call ordering
- Saved order history and customer ledger

## Acknowledgements

Speech recognition and speech synthesis are provided by [Gnani AI](https://www.gnani.ai/) (Prisma and Timbre models), accessed through the Gnani Vachana API.
