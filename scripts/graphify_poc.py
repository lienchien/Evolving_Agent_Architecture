#!/usr/bin/env python3
"""Optional local Graphify smoke test for CEAA. No CEAA runtime dependency.

Runs a code-only AST extraction and optionally executes a Graphify graph query.
Requires the separate 'graphifyy' CLI to be installed on PATH.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter


def run_command(
    args: list[str], *, cwd: Path, env: dict[str, str], timeout: int
) -> tuple[int, float]:
    started = perf_counter()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"ERROR: Graphify command timed out after {timeout}s.", file=sys.stderr)
        return 124, round((perf_counter() - started) * 1000, 2)

    for stream in (completed.stdout, completed.stderr):
        if stream:
            print(stream[-12000:])
    return completed.returncode, round((perf_counter() - started) * 1000, 2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local-only Graphify code graph PoC for CEAA."
    )
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--skip-extract", action="store_true")
    parser.add_argument("--query", help="Optional graphify query to run after indexing.")
    parser.add_argument("--timeout", type=int, default=600, help="Seconds per command.")
    args = parser.parse_args()

    root = args.repo.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"Repository directory does not exist: {root}")
    if args.timeout < 1:
        parser.error("--timeout must be positive")

    binary = shutil.which("graphify")
    if not binary:
        print(
            "Graphify CLI not on PATH. Install with: uv tool install graphifyy",
            file=sys.stderr,
        )
        return 2

    output_dir = root / "graphify-out"
    graph_file = output_dir / "graph.json"
    env = os.environ.copy()
    env["GRAPHIFY_BACKEND"] = "none"  # no semantic model backend

    extraction_ms = None
    if not args.skip_extract:
        print("Running local code-only AST extraction...")
        code, extraction_ms = run_command(
            [binary, "extract", ".", "--code-only"],
            cwd=root, env=env, timeout=args.timeout
        )
        if code:
            return code

    if not graph_file.is_file():
        print(
            f"Expected graph was not found: {graph_file}. "
            "Check the installed Graphify version/output configuration.",
            file=sys.stderr,
        )
        return 3

    try:
        with graph_file.open("r", encoding="utf-8") as handle:
            graph_data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not parse graph.json: {exc}", file=sys.stderr)
        return 4

    meta = graph_data.get("graph", {})
    if not isinstance(meta, dict):
        meta = {}
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "code-only",
        "backend": "none",
        "graph_file": "graphify-out/graph.json",
        "graph_schema_version": meta.get("schema_version"),
        "graphify_version": meta.get("graphify_version"),
        "extraction_ms": extraction_ms,
        "query_executed": bool(args.query),
        "query_return_code": None,
        "query_ms": None,
    }

    if args.query:
        print("Running local graph query...")
        rc, query_ms = run_command(
            [binary, "query", args.query],
            cwd=root, env=env, timeout=args.timeout,
        )
        summary["query_return_code"] = rc
        summary["query_ms"] = query_ms
    else:
        rc = 0

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ceaa-graphify-poc.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
