#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from extractor.inference import infer_stream


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an inferred FollowTheMoney NDJSON stream from a factual stream"
    )
    parser.add_argument("--target", required=True, type=Path, help="Target root directory")
    parser.add_argument(
        "--factual",
        type=Path,
        default=None,
        help="Input factual NDJSON (default: <target>/followthemoney.ndjson)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output inferred NDJSON (default: <target>/followthemoney.inferred.ndjson)",
    )
    parser.add_argument("--ollama-host", type=str, default=None, help="Override Ollama host")
    parser.add_argument("--model", type=str, default=None, help="Override Ollama model")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=8000,
        help="Max characters of evidence text to send to the LLM per item",
    )

    args = parser.parse_args()
    factual = args.factual or (args.target / "followthemoney.ndjson")
    out = args.out or (args.target / "followthemoney.inferred.ndjson")

    return infer_stream(
        factual_ndjson=factual,
        out_path=out,
        ollama_host=args.ollama_host,
        model_name=args.model,
        max_chars=args.max_chars,
    )


if __name__ == "__main__":
    raise SystemExit(main())
