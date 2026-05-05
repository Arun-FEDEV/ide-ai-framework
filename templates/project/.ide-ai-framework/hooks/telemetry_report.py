#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter

from common import events_path


def main() -> int:
    path = events_path()
    if not path.exists():
        print("No telemetry found.")
        return 0
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    counts = Counter(event.get("event", "unknown") for event in events)
    print("IDE AI Framework telemetry")
    for name, count in sorted(counts.items()):
        print(f"- {name}: {count}")
    recent = events[-5:]
    if recent:
        print("\nRecent events:")
        for event in recent:
            print(f"- {event.get('ts')} {event.get('event')} phase={event.get('phase')} gate={event.get('shared_picture_gate')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
