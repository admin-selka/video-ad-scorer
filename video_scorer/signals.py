"""Measured signals: what the video actually does, second by second. No AI, fully deterministic.

- cuts: scene changes (PySceneDetect, threshold tuned for fast Reels editing)
- motion: frame difference energy, sampled once per second
- hook: average motion in the first 3 seconds, where the scroll gets stopped or not
- pacing: the better of cut pace (1 cut every 2s = 100) and motion energy, so both
  single-take UGC and fast slideshows are judged fairly
- audio: loudness per second, and whether the first 3 seconds are silent
"""

import cv2
import librosa
import numpy as np
from scenedetect import ContentDetector, detect


def visual_signals(video_path):
    cuts = [scene[0].get_seconds() for scene in detect(video_path, ContentDetector(threshold=20.0))]

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frames / fps if fps > 0 else 0
    step = int(fps) if fps > 0 else 30

    motion, prev, idx = [], None, 0
    while idx < frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
        score = 0.0
        if prev is not None:
            moved = cv2.threshold(cv2.absdiff(prev, gray), 25, 255, cv2.THRESH_BINARY)[1]
            score = min(round(float(np.sum(moved)) / 10000, 2), 100.0)
        motion.append(score)
        prev = gray
        idx += step
    cap.release()

    hook = float(np.mean(motion[:3])) if motion else 0.0
    cuts_per_min = len(cuts) / duration * 60 if duration else 0
    pacing = max(min(cuts_per_min * 3.33, 100), float(np.mean(motion)) if motion else 0)

    return {
        "duration": round(duration, 2),
        "cut_timestamps": [round(c, 2) for c in cuts],
        "motion_per_second": motion,
        "hook_score": round(hook, 1),
        "pacing_score": int(pacing),
    }


def audio_signals(video_path):
    try:
        y, sr = librosa.load(video_path, sr=None)
    except Exception:
        return {"loudness_db_per_second": [], "silent_hook": True}
    rms = librosa.feature.rms(y=y, hop_length=sr)[0]
    db = [round(float(v), 2) for v in librosa.amplitude_to_db(rms, ref=np.max)]
    first3 = db[:3]
    return {
        "loudness_db_per_second": db,
        "silent_hook": bool((np.mean(first3) if first3 else -100) < -40),
    }
