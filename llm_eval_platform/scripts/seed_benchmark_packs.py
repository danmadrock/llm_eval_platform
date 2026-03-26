from __future__ import annotations

import argparse
import json
from pathlib import Path


PACK_DIR = Path(__file__).resolve().parents[1] / "benchmark_packs"


def main() -> int:
    parser = argparse.ArgumentParser(description="List or export benchmark packs for rapid local setup.")
    parser.add_argument("--list", action="store_true", help="List available benchmark packs")
    parser.add_argument("--name", help="Specific benchmark name without extension")
    parser.add_argument("--output", help="Optional output file for selected benchmark JSON")
    args = parser.parse_args()

    packs = sorted(PACK_DIR.glob("*.json"))
    if args.list:
        for pack in packs:
            print(pack.stem)
        return 0

    if not args.name:
        parser.error("--name is required unless --list is used")

    selected = PACK_DIR / f"{args.name}.json"
    if not selected.exists():
        raise SystemExit(f"Unknown benchmark pack '{args.name}'. Available: {[p.stem for p in packs]}")

    payload = json.loads(selected.read_text())
    if args.output:
        Path(args.output).write_text(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
