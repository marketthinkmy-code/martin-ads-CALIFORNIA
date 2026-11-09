"""Read-only: download Drive videos and save a contact sheet of frames from each.

Used to confirm which Drive file is which scripted video before a build (burned-in
subtitles show the hook line). Env IDS = comma-separated Drive file ids; writes
frames/<n>_<drive id>.jpg plus the file name and duration to the log. With
TRANSCRIBE_SECONDS=N it also prints a speech-to-text of the first N seconds (faster-whisper),
so the opening line can be checked against the script from the log alone.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from adbot.commands import drive_client
from adbot.settings import load_settings

TIMES = [1, 3, 6, 10, 20, 40]          # seconds into the video


def main() -> None:
    ids = [i.strip() for i in os.environ["IDS"].split(",") if i.strip()]
    d = drive_client(load_settings())
    out = Path("frames"); out.mkdir(exist_ok=True)
    tmp = Path("/tmp/vf"); tmp.mkdir(exist_ok=True)
    secs = int(os.environ.get("TRANSCRIBE_SECONDS") or 0)
    model = None
    if secs:
        from faster_whisper import WhisperModel
        model = WhisperModel("small", device="cpu", compute_type="int8")
    for n, fid in enumerate(ids, 1):
        meta = d._svc.files().get(fileId=fid, fields="name,size",
                                  supportsAllDrives=True).execute()
        path = tmp / f"{fid}.mp4"
        d.download_file(fid, path)
        probe = json.loads(subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
            capture_output=True, text=True).stdout or "{}")
        dur = float(probe.get("format", {}).get("duration", 0))
        shots = []
        for t in TIMES:
            if t >= dur:
                continue
            p = tmp / f"{fid}_{t}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(path),
                            "-frames:v", "1", "-vf", "scale=360:-2", str(p)], check=True)
            shots.append(p)
        sheet = out / f"{n}_{fid}.jpg"
        inputs = sum((["-i", str(p)] for p in shots), [])
        cols = 3
        rows = (len(shots) + cols - 1) // cols
        layout = "|".join(f"{'+'.join(['w0'] * (i % cols)) or '0'}_{'+'.join(['h0'] * (i // cols)) or '0'}"
                          for i in range(len(shots)))
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                        f"xstack=inputs={len(shots)}:layout={layout}:fill=black",
                        "-q:v", "4", str(sheet)], check=True)
        print(f"{n}. {fid}  {meta['name']}  {int(meta.get('size', 0))/1e6:.1f}MB  "
              f"{dur:.1f}s  -> {sheet.name} ({rows}x{cols})", flush=True)
        if model:
            wav = tmp / f"{fid}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-t", str(secs),
                            "-ac", "1", "-ar", "16000", str(wav)], check=True)
            segs, _ = model.transcribe(str(wav), language="zh")
            print("   speech: " + " ".join(x.text.strip() for x in segs), flush=True)
            wav.unlink()
        path.unlink()


if __name__ == "__main__":
    main()
