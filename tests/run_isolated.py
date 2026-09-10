"""Run the full Qt regression suite in isolated processes with per-file logs."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", type=Path, default=Path("build/test-results"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    files = args.files or sorted((root / "tests").rglob("test_*.py"))
    if not files or args.timeout <= 0:
        parser.error("Tests and a positive per-file timeout are required")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONUTF8="1")
    results = []
    totals = dict(tests=0, failures=0, errors=0, skipped=0)
    for index, path in enumerate(files, 1):
        path = path.resolve()
        name = str(path.relative_to(root))
        prefix = output / f"{index:03d}-{path.stem}"
        report = prefix.with_suffix(".xml")
        command = [sys.executable, "-m", "pytest", str(path), "-q", "--tb=short",
                   "-o", "faulthandler_timeout=90", f"--junitxml={report}"]
        print(f"[{index}/{len(files)}] {name}", flush=True)
        try:
            completed = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                       errors="replace", timeout=args.timeout)
            code, log = completed.returncode, completed.stdout
        except subprocess.TimeoutExpired as error:
            log = error.stdout or b""
            if isinstance(log, bytes):
                log = log.decode("utf-8", errors="replace")
            code = 124
            log += f"\nTimed out after {args.timeout} seconds: {name}\n"
        prefix.with_suffix(".log").write_text(log, encoding="utf-8")
        print(log, flush=True)
        counts = {}
        if report.exists():
            for suite in ET.parse(report).getroot().iter("testsuite"):
                for key in totals:
                    counts[key] = counts.get(key, 0) + int(suite.get(key, "0"))
            for key, value in counts.items():
                totals[key] += value
        results.append(dict(file=name, exit_code=code, counts=counts))
        (output / "results.json").write_text(
            json.dumps(dict(files=results, totals=totals), indent=2), encoding="utf-8")
    failed = [item["file"] for item in results if item["exit_code"] != 0]
    print(f"Files: {len(files)}; unsuccessful: {len(failed)}; totals: {totals}", flush=True)
    if failed:
        print("Unsuccessful files:\n" + "\n".join(failed), flush=True)
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
