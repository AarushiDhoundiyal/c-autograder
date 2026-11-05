"""Optional profiling and leak checking with valgrind / perf.

callgrind instruction counts are deterministic (same binary + same input ->
same count), so they are safe to use in a grade. perf counters are not, so
they are informational only and off by default.

    python -m agent.profiling samples/add_good.c --input "7 5" [--perf]
"""
from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from agent import sandbox


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def callgrind_instructions(sb, binary, stdin: str, workdir, timeout_s: float = 30):
    """Instructions executed by `binary` (int) or None if it could not be measured."""
    count, outcome = callgrind_run(sb, binary, stdin, workdir, timeout_s)
    return count if outcome == sandbox.OK else None


def callgrind_run(sb, binary, stdin: str, workdir, timeout_s: float = 30):
    """(instructions or None, sandbox outcome) for one run of `binary` under callgrind.
    A run that crashed or timed out is reported with its outcome, so callers can tell the cases apart."""
    if not have("valgrind"):
        return None, None
    fd, out = tempfile.mkstemp(prefix="cg_", suffix=".out", dir=str(workdir))
    Path(out).unlink(missing_ok=True)
    try:
        r = sb.run(["valgrind", "--tool=callgrind", f"--callgrind-out-file={out}", str(binary)],
                   stdin=stdin, time_limit_s=timeout_s, memory_limit_mb=None, nproc=None,
                   cwd=workdir, output_limit_bytes=256 << 20)
    finally:
        Path(out).unlink(missing_ok=True)
        try:
            import os
            os.close(fd)
        except OSError:
            pass
    m = re.search(r"Collected\s*:\s*(\d+)", r.stderr)
    return (int(m.group(1)) if m else None), r.outcome


def memcheck_summary(sb, binary, stdin: str, workdir, timeout_s: float = 60):
    """valgrind memcheck leak summary (second opinion next to LeakSanitizer)."""
    if not have("valgrind"):
        return None
    r = sb.run(["valgrind", "--leak-check=full", "--error-exitcode=0", str(binary)],
               stdin=stdin, time_limit_s=timeout_s, memory_limit_mb=None, nproc=None, cwd=workdir)
    num = lambda pat: int(m.group(1).replace(",", "")) if (m := re.search(pat, r.stderr)) else 0
    return {"definitely_lost_bytes": num(r"definitely lost:\s*([\d,]+) bytes"),
            "indirectly_lost_bytes": num(r"indirectly lost:\s*([\d,]+) bytes"),
            "errors": num(r"ERROR SUMMARY:\s*([\d,]+) errors")}


def perf_instructions(sb, binary, stdin: str, workdir, timeout_s: float = 30):
    """User-space instruction count from `perf stat`, or None. NOT deterministic."""
    if not have("perf"):
        return None
    r = sb.run(["perf", "stat", "-x,", "-e", "instructions:u", str(binary)], stdin=stdin,
               time_limit_s=timeout_s, memory_limit_mb=None, nproc=None, cwd=workdir)
    m = re.search(r"^\s*(\d+),,instructions", r.stderr, re.M)
    return int(m.group(1)) if m else None


def profile_program(sb, binary, stdin: str, workdir, use_perf: bool = False) -> dict:
    info = {"valgrind": have("valgrind"), "perf": have("perf")}
    cg = callgrind_instructions(sb, binary, stdin, workdir)
    if cg is not None:
        info["callgrind_instructions"] = cg
    mc = memcheck_summary(sb, binary, stdin, workdir)
    if mc is not None:
        info["memcheck"] = mc
    if use_perf:
        pi = perf_instructions(sb, binary, stdin, workdir)
        if pi is not None:
            info["perf_instructions"] = pi
    return info


def main(argv=None) -> int:
    import argparse
    import json
    from agent import sandbox
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--input", default="7 5\n")
    ap.add_argument("--perf", action="store_true")
    a = ap.parse_args(argv)
    sb = sandbox.Sandbox(10, 256)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(a.source).resolve()
        out = Path(tmp) / "p.bin"
        comp = sb.compile(src, out, ["-g", "-O0", "-std=c11"], cwd=src.parent)
        if not comp.ok:
            print("does not compile:", *comp.errors[:3], sep="\n  ")
            return 1
        print(json.dumps(profile_program(sb, out, a.input.replace("\\n", "\n"), tmp, a.perf), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
