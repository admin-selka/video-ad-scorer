"""AI audit: Gemini watches the video with the Whisper transcript and the rule files,
and returns the creative read plus anything likely to get the ad rejected or taxed.
"""

import json
import os
import time

import google.generativeai as genai

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


def load_rules():
    text = ""
    for name in sorted(os.listdir(RULES_DIR)):
        if name.endswith(".txt"):
            with open(os.path.join(RULES_DIR, name), encoding="utf-8") as f:
                text += f"\n=== {name} ===\n{f.read()}"
    return text


PROMPT = """
You audit Facebook and Instagram video ads.

Rules to enforce:
{rules}

Task:
1. Watch the video and read the transcript below.
2. Delivery penalties: text over 20% of the frame, fake UI elements, bait tactics from the penalties file.
3. Policy risks: before/after imagery, zoomed-in body parts, unrealistic claims like "cure".
4. Creative read: hook type, narrative arc, tone, call to action.
5. If the audio isn't English, add "native_script": the spoken words in Latin script
   (Hindi as Hinglish, no Devanagari). Otherwise null.

Return one JSON object with exactly these keys:
{{
  "hook_type": "e.g. Pattern Interrupt, Problem/Solution, UGC Testimonial",
  "narrative_arc": "one sentence",
  "tone": "e.g. Aggressive, Clinical, Hype, Relaxed",
  "call_to_action": "the CTA, or 'None detected'",
  "transcript_summary": "one sentence",
  "native_script": null,
  "delivery_penalties": [{{"timestamp": "MM:SS", "issue": "", "detail": ""}}],
  "policy_risks": [{{"timestamp": "MM:SS", "severity": "HIGH_RISK or BAN_RISK", "rule": "", "fix": ""}}],
  "director_insight": "two sentences on why this will fail or win, based on pacing and emotion"
}}

Transcript (English translation):
{transcript}
"""


class GeminiAudit:
    def __init__(self, model=None):
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(
            model_name=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            generation_config={"temperature": 0.0, "max_output_tokens": 4096,
                               "response_mime_type": "application/json"},
        )
        self.rules = load_rules()

    def run(self, video_path, transcript):
        video = genai.upload_file(video_path)
        while video.state.name == "PROCESSING":
            time.sleep(1)
            video = genai.get_file(video.name)
        response = self.model.generate_content([video, PROMPT.format(rules=self.rules, transcript=transcript)])
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"error": "model returned invalid JSON", "raw": response.text}
