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
        narrations      = self._create_narrations(slides_json)
        html_path = self._markdown_to_reveal(md, len(slides_json['slides']), slides_dir)
        self._create_audio(narrations, audio_dir)   # pass narrations list
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

    def _create_narrations(self, slides_json):
        resp = self.client.responses.create(
            model=OPENAI_MODEL_LLM,
            instructions=(
                "You are an expert narrator. For each slide JSON object give a"
                " spoken‑word narration string that briefly explains the materials on the slide concering the topic {topic}. Respond ONLY with JSON:"
                "{ narrations:[{slide_index:int,text:str},...] }"
            ),
            input=json.dumps(slides_json["slides"]),
        )
        return json.loads(resp.output_text)["narrations"]

    def _markdown_to_reveal(self, md: str, slide_count: int, out_dir: Path) -> Path:
        # 1) Generate raw HTML via Pandoc
        html_tmp = out_dir / "raw.html"
        pypandoc.convert_text(
            md,
            to="html",
            format="md",
            outputfile=str(html_tmp),
            extra_args=[
                "-t", "revealjs", "-s",
                "--metadata", "title=Deck",
                "-V", "revealjs-url=https://cdn.jsdelivr.net/npm/reveal.js@4.6.1",
                "-V", "revealjs-theme=black"
            ],
        )
    
        # 2) Read it and split on <section>
        html_final = out_dir / "index.html"
        html_txt    = html_tmp.read_text(encoding="utf8")
        parts       = html_txt.split("<section")
        rebuilt     = parts[0]
    
        # 3) Rebuild each section with the correct audio attrs
        for idx, fragment in enumerate(parts[1:]):
            if idx < slide_count:
                rebuilt += (
                    f'<section data-audio="../audio/slide{idx}.mp3" data-autoslide="5000"'
                    + fragment
                )
            else:
                rebuilt += "<section" + fragment
    
        # 4) Inject your JS snippet before </body>
        js_snippet = (Path(__file__).parent / "templates" / "js_snippet.html").read_text()
        rebuilt = rebuilt.replace("</body>", js_snippet + "\n</body>")
    
        # 5) Write and clean up
        html_final.write_text(rebuilt, encoding="utf8")
        html_tmp.unlink(missing_ok=True)
        return html_final


    def _create_audio(self, slides_json: dict, audio_dir: Path):
        
        for item in narrations:
            idx  = item["slide_index"]
            text = item["text"]

            # Ensure we have a string, not a list
            if isinstance(raw_content, list):
                text = " \n".join(raw_content)
            else:
                text = str(raw_content)

            out_file = audio_dir / f"slide{idx}.mp3"
            with self.client.audio.speech.with_streaming_response.create(
                model=OPENAI_MODEL_TTS,
                input=text,                # now guaranteed to be a string
                voice=VOICE,
                instructions="Narrate the following text in a clear, engaging tone with natural pacing.",
                response_format="mp3",
            ) as r:
                r.stream_to_file(out_file)

