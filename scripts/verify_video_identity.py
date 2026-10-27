"""Read-only: prove a Drive export is the same cut a Meta ad video ran, frame by frame.

Duration alone can coincide (re-exports, subtitle variants), so this downloads both files,
grabs frames at fixed timestamps, shrinks them to 32x32 grayscale and reports the mean pixel
difference per frame (0 = identical picture, ~>20 = clearly different shot). Also lists the
Drive file's revisions, since a file edited after the ad launched may no longer be that cut.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import requests

from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import load_settings

# every Meta video id seen behind each winner ad; the first one whose `source` is readable is used
PAIRS = [
    ("V1 华人孩子在美国", ["4065966730323187", "1908705869717276", "1949496062433268",
                        "4178562869108616"], "1LpfDhu-5Xn6_F9vM-5cc9x5CdT1I9T9d"),
    ("V3 175以上",       ["1439172857608022", "1297858878774827", "28725175003738688"],
     "1xTxHqOPqHaZKdgs1kAn5Nsi2R_iVvK1f"),
]
STAMPS = [2, 10, 25, 45, 65, 85]
WORK = Path("/tmp/verify"); WORK.mkdir(exist_ok=True)


def frame(path: Path, t: float) -> bytes:
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
         "-vf", "scale=32:32,format=gray", "-f", "rawvideo", "-"],
        check=True, capture_output=True).stdout


def main() -> None:
    s = load_settings()
    g = graph_client(s)
    drive = DriveClient(s.secrets.google_sa_json)
    for label, vids, fid in PAIRS:
        vid, src = None, None
        for v in vids:
            try:
                src = g.get_object(v, "source").get("source")
            except Exception as e:  # noqa: BLE001
                print(f"  {v}: {str(e)[:80]}")
            if src:
                vid = v
                break
            print(f"  {v}: no downloadable source")
        if not src:
            print(f"=== {label}: no Meta video downloadable — cannot frame-compare ===\n")
            continue
        print(f"=== {label}: Meta video {vid}  vs  Drive {fid} ===")
        mp = WORK / f"{vid}.mp4"
        with requests.get(src, stream=True, timeout=300) as r:
            r.raise_for_status()
            mp.write_bytes(r.content)
        dp = drive.download_file(fid, WORK / f"{fid}.mp4")
        print(f"  sizes: meta {mp.stat().st_size/1e6:.1f}MB · drive {Path(dp).stat().st_size/1e6:.1f}MB")
        diffs = []
        for t in STAMPS:
            a, b = frame(mp, t), frame(Path(dp), t)
            if not a or not b or len(a) != len(b):
                print(f"  t={t:>3}s  could not compare")
                continue
            d = sum(abs(x - y) for x, y in zip(a, b)) / len(a)
            diffs.append(d)
            print(f"  t={t:>3}s  mean pixel diff {d:6.2f}")
        if diffs:
            verdict = "SAME CUT" if max(diffs) < 8 else ("DIFFERENT" if min(diffs) > 20 else "PARTLY DIFFERENT")
            print(f"  -> max diff {max(diffs):.2f} · verdict: {verdict}")
        try:
            revs = drive._svc.revisions().list(fileId=fid, fields="revisions(id,modifiedTime,size)").execute()
            for rv in revs.get("revisions", []):
                print(f"  revision {rv.get('id')} modified {rv.get('modifiedTime')} size {rv.get('size')}")
        except Exception as e:  # noqa: BLE001
            print(f"  revisions unreadable: {str(e)[:90]}")
        print()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
