#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from extractor.dedup import dedup_stream


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate/merge an inferred FollowTheMoney NDJSON stream"
    )
    parser.add_argument("--target", required=True, type=Path, help="Target root directory")
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=None,
        help="Input inferred NDJSON (default: <target>/followthemoney.inferred.ndjson)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output deduped NDJSON (default: <target>/followthemoney.inferred.dedup.ndjson)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress to stderr",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    in_path = args.in_path or (args.target / "followthemoney.inferred.ndjson")
    out_path = args.out or (args.target / "followthemoney.inferred.dedup.ndjson")

    return dedup_stream(in_path=in_path, out_path=out_path, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
