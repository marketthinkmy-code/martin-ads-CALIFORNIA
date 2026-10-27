"""Read-only: find which Drive export is the exact cut each US winner ad ran.

File names in the editor's folders don't settle it (the same video number is reused across
the Dec-2025 「加州」 batch and the Feb-2026 「Martin 26'」 batch), so this matches on duration:
every distinct video behind the winner ads in the California account (with its length) vs the
videoMediaMetadata duration of each candidate Drive file. Prints names, ids and seconds only.
"""
from __future__ import annotations

from collections import defaultdict

from adbot.clients.drive import DriveClient
from adbot.commands import graph_client
from adbot.settings import load_settings

CA = "act_1629566827721449"
WINNERS = {"V1 华人孩子在美国": ("华人孩子在美国",), "V3 175以上": ("175以上",),
           "吃饭喝水": ("吃饭喝水", "吃飯喝水")}
CANDIDATES = {
    "1LpfDhu-5Xn6_F9vM-5cc9x5CdT1I9T9d": "马丁美国 Video 1 (Dec-25)",
    "1gSqqOapM4xDgctWLW8pTYpeFo42_FdyW": "马丁加州Video 2 (Dec-25)",
    "1dM0dXYRvYYsvG4efGpIBDfoua5Ph8B2z": "马丁加州Video 3 (Dec-25)",
    "1jGy3GmylBuLDNS5nNHTtMqXTfhPq9r0L": "马丁加州Video 4 (Dec-25)",
    "141VqPYl1-ImujfonQB8QLRa-1d9WLVf4": "Martin 26' Video 1 California",
    "1kUb5621BGA24Gd4x-_IWpstV9TLTvErc": "Martin 26' Video 2 California",
    "1xTxHqOPqHaZKdgs1kAn5Nsi2R_iVvK1f": "Martin 26' Video 3 California",
    "1Oqezu33tZj8ApUxXfa7UaG-M9cvw2pwb": "Martin 26' Video 5",
    "1bTi962ChGREEKI9KstWqJnUMHgTYLMrs": "Martin 26' Video 6 California",
    "1JxvI_jIqwsND-vRam1nIHztnxK5HdtUO": "Martin 26' Video 7",
    "1mVWeExLCdYQhLDFjAqP0wvU0McghV_3t": "Martin 26' Video 9 California",
    "1dNgWhloG2wcHkD_y_sq8_ldWOP_iD1Mv": "Martin 26' Video 10 California",
    "1SWXi8rWU1BuwfEv-SVbq912A2uVfypkX": "Hook 5Y (Jan-26)",
    "1KXBajUavJbKUvM5VJct0gBH2onjKfau_": "馬丁溫哥華v4 (Dec-25)",
    "1WJx1bNWHp_ht6LWoqh1qDUtc8d7E-xVf": "馬丁溫哥華v1 (Dec-25)",
}


def main() -> None:
    s = load_settings()
    g = graph_client(s)

    vids = defaultdict(set)
    for ad in g._get_all(f"{CA}/ads", {"fields": "name,creative{video_id,object_story_spec}",
                                       "limit": 200}):
        name = ad.get("name", "")
        label = next((k for k, keys in WINNERS.items() if any(t in name for t in keys)), None)
        if not label:
            continue
        cr = ad.get("creative") or {}
        vid = cr.get("video_id") or (((cr.get("object_story_spec") or {}).get("video_data")) or {}).get("video_id")
        if vid:
            vids[label].add(vid)

    print("=== Meta videos behind the winner ads (California account) ===")
    meta_len = {}
    for label, ids in vids.items():
        for vid in sorted(ids):
            try:
                v = g.get_object(vid, "length,created_time")
                meta_len[vid] = float(v.get("length") or 0)
                print(f"  {label:18} video {vid}  {meta_len[vid]:7.2f}s  created {v.get('created_time')}")
            except Exception as e:  # noqa: BLE001
                print(f"  {label:18} video {vid}  unreadable: {e}")

    print("\n=== Drive candidates (duration) ===")
    svc = DriveClient(s.secrets.google_sa_json)._svc
    drive_len = {}
    for fid, label in CANDIDATES.items():
        try:
            f = svc.files().get(fileId=fid, fields="name,videoMediaMetadata",
                                supportsAllDrives=True).execute()
            ms = (f.get("videoMediaMetadata") or {}).get("durationMillis")
            drive_len[fid] = int(ms) / 1000 if ms else None
            print(f"  {label:32} {fid}  {drive_len[fid] if drive_len[fid] else '—':>8}s")
        except Exception as e:  # noqa: BLE001
            print(f"  {label:32} {fid}  no access: {str(e)[:80]}")

    print("\n=== Matches (|Δ| ≤ 1.0s) ===")
    for label, ids in vids.items():
        for vid in sorted(ids):
            ml = meta_len.get(vid)
            if not ml:
                continue
            hits = [(abs(ml - dl), fid) for fid, dl in drive_len.items() if dl and abs(ml - dl) <= 1.0]
            hits.sort()
            txt = ", ".join(f"{CANDIDATES[f]} (Δ{d:.2f}s) https://drive.google.com/file/d/{f}/view"
                            for d, f in hits) or "no Drive match"
            print(f"  {label:18} {vid} {ml:.2f}s -> {txt}")


if __name__ == "__main__":
    main()
