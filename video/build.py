# -*- coding: utf-8 -*-
"""Build the CoffeeJeV explainer videos (zh + en) end to end.

Pipeline per language:
  1. edge-tts each sentence -> mp3 (exact caption timing)
  2. compute per-language timeline (scene starts, captions)
  3. Playwright deterministic frame capture (24 fps, 1920x1080 jpeg)
  4. ffmpeg: frames + narration + ambient pad -> h264 mp4 (+ .vtt captions)
"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

import edge_tts
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from narration import ORDER, SCRIPT, VOICE  # noqa: E402

ROOT = Path(__file__).resolve().parent
FPS = 24
SENT_GAP = 0.24      # gap between sentences inside a scene (s)
SCENE_LEAD = 0.85    # silence before a scene's first sentence (s)
SCENE_TAIL = 1.25    # silence after a scene's last sentence (s)
FIRST_OFFSET = 0.9   # video lead-in before scene 1
INTER_SCENE = 0.35   # extra gap between scenes


def ffprobe_dur(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


async def tts_all() -> None:
    for lang in ("zh", "en"):
        outdir = ROOT / "tts" / lang
        outdir.mkdir(parents=True, exist_ok=True)
        for sid in ORDER:
            for i, sent in enumerate(SCRIPT[sid][lang]):
                f = outdir / f"{sid}_{i:02d}.mp3"
                if f.exists() and f.stat().st_size > 0:
                    continue
                await edge_tts.Communicate(sent, VOICE[lang]).save(str(f))
                print("tts", lang, sid, i, flush=True)


def build_timeline(lang: str) -> dict:
    """Return {scenes:[{id,t0,t1,caps}], total, sent_offsets:{sid:[(mp3,at)]}}."""
    t = FIRST_OFFSET
    scenes, audio_plan = [], []
    for n, sid in enumerate(ORDER):
        files = sorted((ROOT / "tts" / lang).glob(f"{sid}_*.mp3"))
        durs = [ffprobe_dur(f) for f in files]
        lead = SCENE_LEAD if n else 0.35
        scene_t0 = t
        at = scene_t0 + lead
        caps = []
        for f, d in zip(files, durs):
            audio_plan.append((f, at))
            caps.append([at - scene_t0, at - scene_t0 + d + 0.25,
                         " ".join(f.stem.split("_")[:1]) and ""])
            caps[-1][2] = None  # fill later
            at += d + SENT_GAP
        last_end = at - SENT_GAP
        scene_t1 = last_end + SCENE_TAIL + (INTER_SCENE if n < len(ORDER) - 1 else 0)
        # captions (sentence text in order)
        for k, sent in enumerate(SCRIPT[sid][lang]):
            caps[k][2] = sent
        scenes.append({"id": sid, "t0": scene_t0, "t1": scene_t1, "caps": caps})
        t = scene_t1
    return {"lang": lang, "scenes": scenes, "total": t, "audio": audio_plan}


def build_audio(lang: str, plan, total: float) -> Path:
    """One ffmpeg run: adelay every sentence, mix, plus ambient pad."""
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    narr = out / f"narration_{lang}.wav"
    pad = out / f"pad_{lang}.wav"
    pad_dur = f"{total + 1:.2f}"

    inputs, filters, labels = [], [], []
    for i, (f, at) in enumerate(plan):
        inputs += ["-i", str(f)]
        ms = int(round(at * 1000))
        filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}:all=1[s{i}]")
        labels.append(f"[s{i}]")
    # ambient pad: soft Am add9-ish drone
    filters.append(
        "aevalsrc=0.20*sin(2*PI*110*t)+0.13*sin(2*PI*164.81*t)+0.09*sin(2*PI*220*t)"
        "+0.07*sin(2*PI*329.63*t)+0.05*sin(2*PI*246.94*t):s=48000:d=" + pad_dur +
        ",lowpass=f=850,tremolo=f=0.11:d=0.4,volume=0.055,"
        f"afade=t=in:d=4,afade=t=out:st={total - 5:.2f}:d=5,aformat=channel_layouts=stereo[pd]")
    filters.append("".join(labels) + f"amix=inputs={len(plan)}:normalize=0[mix]")
    filters.append(f"[mix][pd]amix=inputs=2:normalize=0[aout]")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error"] + inputs +
        ["-filter_complex", ";".join(filters), "-map", "[aout]",
         "-t", f"{total:.2f}", "-c:a", "pcm_s16le", str(narr)],
        check=True)
    print("audio done", narr, flush=True)
    return narr


def write_vtt(lang: str, tl: dict) -> Path:
    def ts(x: float) -> str:
        h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"
    vtt = ["WEBVTT", ""]
    for sc in tl["scenes"]:
        for a, b, txt in sc["caps"]:
            vtt += [f"{ts(sc['t0']+a)} --> {ts(sc['t0']+min(b, sc['t1']-sc['t0']))}", txt, ""]
    p = ROOT / "out" / f"coffeejev-{lang}.vtt"
    p.write_text("\n".join(vtt), encoding="utf-8")
    return p


def capture_frames(lang: str, tl: dict) -> Path:
    frames = ROOT / "frames" / lang
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir(parents=True)
    url = (ROOT / "scene.html").resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", args=["--force-device-scale-factor=1"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(900)
        pg.evaluate("tl => window.setTimeline(tl)", tl)
        pg.evaluate("window.renderAt(0)")
        pg.wait_for_timeout(400)
        n = int(tl["total"] * FPS)
        import time
        t0 = time.time()
        for i in range(n):
            pg.evaluate("t => window.renderAt(t)", i / FPS)
            pg.screenshot(path=str(frames / f"{i:05d}.jpg"), type="jpeg", quality=93)
            if i % 240 == 0:
                rate = (i + 1) / (time.time() - t0)
                print(f"[{lang}] frame {i}/{n} ({rate:.1f} fps cap, eta {((n-i)/max(rate,.1))/60:.1f} min)", flush=True)
        b.close()
    return frames


def encode(lang: str, tl: dict, frames: Path) -> Path:
    out = ROOT / "out"
    mp4 = out / f"coffeejev-explainer-{lang}.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
         "-i", str(frames / "%05d.jpg"),
         "-i", str(out / f"narration_{lang}.wav"),
         "-filter_complex", "[1:a]anull[a]",
         "-map", "0:v", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", str(mp4)],
        check=True)
    print("encoded", mp4, flush=True)
    return mp4


def main() -> None:
    only = sys.argv[1:] or ["zh", "en"]
    asyncio.run(tts_all())
    for lang in only:
        tl = build_timeline(lang)
        (ROOT / "out").mkdir(exist_ok=True)
        (ROOT / "out" / f"timeline_{lang}.json").write_text(
            json.dumps({k: v for k, v in tl.items() if k != "audio"},
                       ensure_ascii=False, indent=1), encoding="utf-8")
        build_audio(lang, tl["audio"], tl["total"])
        write_vtt(lang, tl)
        frames = capture_frames(lang, tl)
        encode(lang, tl, frames)
        print(f"NOTE: frame cache kept at {frames} (delete manually if disk is tight)", flush=True)
        print(f"DONE {lang}: {tl['total']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
