import json, os, re
from pathlib import Path
import pypandoc
from openai import OpenAI

OPENAI_MODEL_LLM = "gpt-4.1-mini"
OPENAI_MODEL_TTS = "gpt-4o-mini-tts"
VOICE = "alloy"

class PresentationManager:
    def __init__(self):
        # Retrieve OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable not set")
        # Initialize OpenAI client with explicit API key
        self.client = OpenAI(api_key=api_key)
        self.base_dir = Path(__file__).parent / "static" / "generated"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, topic: str, depth: str, pres_id: str) -> None:
        work_dir = self.base_dir / pres_id
        slides_dir = work_dir / "slides"
        audio_dir = work_dir / "audio"
        slides_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(exist_ok=True)

        slides_json, md = self._create_outline(topic, depth)
        html_path = self._markdown_to_reveal(md, len(slides_json['slides']), slides_dir)
        self._create_audio(slides_json, audio_dir)
        print(f"Presentation ready → {html_path.relative_to(self.base_dir.parent)}")

    # ----------------- helpers -----------------
    def _create_outline(self, topic: str, depth: str):
        instructions = (
            "You are a professional presentation architect. "
            "Produce a slide deck outline on a given topic and depth, first in structured JSON and then in Markdown."
        )
        inp = f"Topic: {topic}\nDepth: {depth}"
        resp = self.client.responses.create(
            model=OPENAI_MODEL_LLM,
            instructions=instructions,
            input=inp,
        )
        raw = resp.output_text.strip()

        # Expecting format: ```json ... ``` followed by markdown
        try:
            json_part = raw.split("```json", 1)[1].split("```", 1)[0]
            md_part = raw.split("```", 2)[2].strip()
        except IndexError:
            raise ValueError("Unexpected outline format; ensure JSON fence comes first.")

        slides_json = json.loads(json_part)
        return slides_json, md_part

    def _markdown_to_reveal(self, md: str, slide_count: int, out_dir: Path) -> Path:
        html_tmp = out_dir / "raw.html"
        pypandoc.convert_text(
            md,
            to="html",
            format="md",
            outputfile=str(html_tmp),
            extra_args=["-t", "revealjs", "-s", "--metadata", "title=Deck"],
        )
        html_final = out_dir / "index.html"
        audio_attrs = [
            f'data-audio="../audio/slide{i}.mp3" data-autoslide="5000"'
            for i in range(slide_count)
        ]
        html_txt = html_tmp.read_text(encoding="utf8")
        for attr in audio_attrs:
            html_txt = html_txt.replace("<section", f"<section {attr}", 1)
        # insert js snippet
        snippet_path = Path(__file__).parent / "templates" / "js_snippet.html"
        js_snippet = snippet_path.read_text()
        html_txt = html_txt.replace("</body>", js_snippet + "\n</body>")
        html_final.write_text(html_txt, encoding="utf8")
        html_tmp.unlink(missing_ok=True)
        return html_final

    def _create_audio(self, slides_json: dict, audio_dir: Path):
        slides = slides_json.get("slides", [])
        for idx, slide in enumerate(slides):
            text = slide.get("content", "")
            out_file = audio_dir / f"slide{idx}.mp3"
            with self.client.audio.speech.with_streaming_response.create(
                model=OPENAI_MODEL_TTS,
                input=text,
                voice=VOICE,
                instructions="Narrate the following text in a clear, engaging tone with natural pacing.",
                response_format="mp3",
            ) as r:
                r.stream_to_file(out_file)
