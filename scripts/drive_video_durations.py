"""Read-only: print name, size and duration of the videos in a Drive folder.

Used to tell apart editor exports that arrive with random file names, by matching their
length against known ad videos. Prints metadata only.
"""
from __future__ import annotations

import sys

from adbot.clients.drive import DriveClient
from adbot.settings import load_settings


def main() -> None:
    folder = sys.argv[1]
    svc = DriveClient(load_settings().secrets.google_sa_json)._svc
    try:
        kids = svc.files().list(q=f"'{folder}' in parents and trashed = false",
                                fields="files(id,name,size,videoMediaMetadata)",
                                supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    except Exception as e:  # noqa: BLE001
        print(f"folder unreadable by the service account: {str(e)[:120]}")
        return
    files = kids.get("files", [])
    if not files:
        print("service account sees no files here (folder not shared with it?)")
    for f in files:
        vm = f.get("videoMediaMetadata") or {}
        ms = vm.get("durationMillis")
        print(f"{f['id']}  {f['name']}  {int(f.get('size', 0))/1e6:.1f}MB  "
              f"{int(ms)/1000 if ms else '—'}s  {vm.get('width')}x{vm.get('height')}")


if __name__ == "__main__":
    main()
