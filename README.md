# Video Ad Scorer

Score a short-form video ad (Reels, Stories, TikTok-style) before it runs: is the hook strong, is the pacing right, and is anything in it likely to get the ad rejected or make it cost more to deliver?

It combines **measured signals** (what the video actually does, second by second) with an **AI audit** (what a senior media buyer would say about it).

Example output (numbers are illustrative):

```
$ python score_video.py examples/ad.mp4
{
  "duration": 18.4,
  "scores": { "hook": 64.2, "pacing": 71, "policy": "RISK" },
  "hook": { "silent_start": false, "cuts_in_first_3s": 2, "note": "Audio starts strong." },
  "timeline": { "motion_per_second": [...], "loudness_db_per_second": [...], "cut_timestamps": [...] },
  "transcript": [ { "start": 0.0, "end": 2.4, "text": "..." } ],
  "audit": {
    "hook_type": "Problem/Solution",
    "tone": "Hype",
    "policy_risks": [ { "timestamp": "00:07", "severity": "HIGH_RISK", "rule": "...", "fix": "..." } ],
    "director_insight": "..."
  }
}
```

## How it works

**1. Measured signals** (local, deterministic, no AI)
- **Cuts:** scene changes with PySceneDetect, tuned for fast Reels editing.
- **Motion:** frame difference energy, once per second.
- **Hook score:** average motion in the first 3 seconds, where the scroll gets stopped or not.
- **Pacing score:** the better of cut pace (one cut every 2 seconds = 100) and overall motion, so single-take UGC and fast slideshows are both judged fairly.
- **Audio:** loudness per second, and a flag if the first 3 seconds are silent.

**2. Transcript.** Whisper transcribes the audio and translates it to English, with timestamps, so the audit works for any spoken language.

**3. AI audit.** Gemini 2.5 Flash watches the video, reads the transcript and checks it against two rule files:
- `rules/meta_ad_policy_summary.txt`: a working summary of Meta's ad standards.
- `rules/delivery_penalties.txt`: patterns that raise CPM or limit reach (text-heavy frames, fake UI, bait).

It returns the hook type, narrative arc, tone, CTA, timestamped policy risks with fixes, and a short director's note. Temperature 0, so the same video gets the same read. Non-English audio also gets a Latin-script version of the script (Hindi comes back as Hinglish).

## Quick start

```
pip install -r requirements.txt        # also needs ffmpeg on your PATH
cp .env.example .env                   # add GOOGLE_API_KEY, or use --no-llm

python score_video.py your_ad.mp4
python score_video.py your_ad.mp4 --no-llm --whisper small
```

## Layout

```
score_video.py            CLI
video_scorer/
  __init__.py             score_video(): runs everything and merges the result
  signals.py              cuts, motion, hook, pacing, audio
  audit.py                Gemini audit
  rules/                  policy summary + delivery penalties (edit these to change what gets flagged)
```

## Background

Built in Dec 2025 and Jan 2026 as the video side of an ad creative product I was working on, then set aside. Cleaned up and published in Nov 2026. The rule files are summaries and practitioner heuristics, not official Meta text.

MIT licensed.
