# GPT‑Powered Reveal.js Presentation Generator (POC)

A minimal Flask web app that dynamically generates **Reveal.js** slide decks with synchronized narration using OpenAI’s GPT and TTS APIs.

---
## Features

- **Topic + Depth input**: User provides a topic and selects `intro` / `intermediate` / `advanced`.
- **Automated outline**: Uses **gpt-4.1-mini** (Responses API) to output a structured JSON slide outline & Markdown.
- **Slide rendering**: Converts Markdown to a standalone **Reveal.js** presentation via Pandoc.
- **Per‑slide audio**: Calls **gpt-4o-mini-tts** to create one MP3 per slide for narration.
- **Player UI**: Embedded Reveal.js deck with audio sync and basic controls (Pause, Restart, Mute, Exit).

---
## Requirements

- Python 3.10+
- Flask >= 2.3
- openai >= 1.14
- pypandoc >= 1.12
- python-dotenv >= 1.0 (optional)

---
## Installation

```bash
git clone https://your-repo-url.git
cd presentation_poc
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Create a `.env` (or set env vars) with:
```
OPENAI_API_KEY="sk-..."
```

---
## Usage

```bash
python app.py
```

Open http://localhost:5000 in your browser, enter a topic and depth, and click **Generate**. The app will:

1. Show a loading overlay with status updates.
2. Render and save slides + audio under `static/generated/<uuid>/`.
3. Redirect to the presentation player with manual start.

---
## Project Structure

```plaintext
presentation_poc/
├─ app.py                # Flask routes & orchestrator
├─ presentation.py       # Core pipeline: outline, markdown→HTML, TTS
├─ requirements.txt
├─ templates/
│   ├─ index.html        # Input form
│   └─ player.html       # Embeds generated Reveal deck
└─ static/generated/     # Outputs saved per presentation UUID
```

---
## Controls & UX

- **Overlay**: displays generation steps, requires manual **Start Presentation**.
- **Controls**: Pause/Play, Restart, Mute/Unmute, Exit.
- **Sync**: per‑slide audio files keep narration aligned with slide changes.

---
## Future Improvements

- Async task queue (Celery / RQ) for long decks
- Per‑slide image generation (Replicate API)
- Structured Outputs / function‑calling for robust JSON parsing
- Persistent storage & user authentication
- Dockerization & CI/CD pipeline


