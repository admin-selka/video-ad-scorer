"""Scores a short-form video ad (Reels, Stories, TikTok-style) before it runs."""

import os

from .signals import audio_signals, visual_signals


def transcribe(video_path, size="base"):
    import whisper

    result = whisper.load_model(size).transcribe(video_path, task="translate")
    segments = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
                for s in result["segments"]]
    return result["text"].strip(), segments


def score_video(video_path, use_llm=True, whisper_size="base"):
    visual = visual_signals(video_path)
    audio = audio_signals(video_path)
    text, segments = transcribe(video_path, whisper_size)

    audit = None
    if use_llm:
        from .audit import GeminiAudit
        audit = GeminiAudit().run(video_path, text)

    cuts_in_hook = len([t for t in visual["cut_timestamps"] if t < 3.0])
    return {
        "file": os.path.basename(video_path),
        "duration": visual["duration"],
        "scores": {
            "hook": visual["hook_score"],
            "pacing": visual["pacing_score"],
            "policy": None if audit is None else ("RISK" if audit.get("policy_risks") else "CLEAR"),
        },
        "hook": {
            "silent_start": audio["silent_hook"],
            "cuts_in_first_3s": cuts_in_hook,
            "note": "Silent first 3 seconds, most viewers will scroll past." if audio["silent_hook"] else "Audio starts strong.",
        },
        "timeline": {
            "motion_per_second": visual["motion_per_second"],
            "loudness_db_per_second": audio["loudness_db_per_second"],
            "cut_timestamps": visual["cut_timestamps"],
        },
        "transcript": segments,
        "audit": audit,
    }
