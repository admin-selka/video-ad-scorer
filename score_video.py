"""Score a video ad from the command line.

    python score_video.py ad.mp4
    python score_video.py ad.mp4 --no-llm      # measured signals + transcript only
"""

import argparse
import json

from dotenv import load_dotenv

from video_scorer import score_video


def main():
    load_dotenv()
    p = argparse.ArgumentParser(description="Score a short-form video ad before it runs.")
    p.add_argument("video")
    p.add_argument("--no-llm", action="store_true", help="skip the Gemini audit (no API key needed)")
    p.add_argument("--whisper", default="base", help="Whisper model size: tiny, base, small, medium")
    args = p.parse_args()
    print(json.dumps(score_video(args.video, use_llm=not args.no_llm, whisper_size=args.whisper), indent=2))


if __name__ == "__main__":
    main()
