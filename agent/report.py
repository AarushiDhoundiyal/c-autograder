"""Report writers: machine-readable JSON and the student-facing text report.
Nothing time-dependent is stored, so identical inputs give identical files."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def tool_versions() -> dict:
    def first_line(cmd):
        if shutil.which(cmd[0]) is None and cmd[0] != sys.executable:
            return "not installed"
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            text = (out.stdout or out.stderr).strip().splitlines()
            return text[0] if text else "unknown"
        except Exception:  # noqa: BLE001
            return "unknown"
    return {"gcc": first_line(["gcc", "--version"]),
            "cppcheck": first_line(["cppcheck", "--version"]),
            "lizard": first_line([sys.executable, "-m", "lizard", "--version"]),
            "valgrind": first_line(["valgrind", "--version"]),
            "python": sys.version.split()[0]}


def report_to_json(report: dict) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n"


def _show(x) -> str:
    s = str(x).rstrip("\n")
    return s if s else "(no output)"


def _wrap(prefix: str, text: str, width: int = 72) -> list:
    words, lines, cur = text.split(), [], prefix
    indent = " " * len(prefix)
    for w in words:
        if len(cur) + len(w) + 1 > width and cur.strip():
            lines.append(cur.rstrip())
            cur = indent
        cur += w + " "
    lines.append(cur.rstrip())
    return lines


def render_text(report: dict) -> str:
    L = [f"===== Grading report for {report['submission']} =====",
         f"Overall grade: {report['grade']:g} / 100" + ("   [PARTIAL: some metrics could not be graded]" if report["partial"] else "")]
    fp = report["first_pass"]
    for note in fp.get("notes", []):
        L.append(f"Note: {note}")
    for err in fp.get("compile_errors", [])[:3]:
        L.append(f"  compiler: {err}")
    L += ["", f"{'Metric':<16}{'Weight':>7}{'Score':>9}{'Points':>9}  Comment"]
    for m in report["metrics"]:
        w = m["weight"] * 100
        pts = f"{m['contribution']:g}/{w:g}"
        status = "" if m["status"] == "ok" else f"[{m['status']}] "
        L.append(f"{m['name']:<16}{w:>6g}%{m['score']:>9.2f}{pts:>9}  {status}{m['feedback']}")

    fails = [(m["name"], f) for m in report["metrics"]
             for f in m["evidence"].get("failing", []) if isinstance(f, dict)]
    if fails:
        L += ["", "--- Where you failed ---"]
        for name, f in fails[:3]:
            label = f.get("test")
            L.append(f"[{name}]" + (f" test {label}" if label else ""))
            L.append(f"INPUT:    {_show(f.get('input', ''))}")
            L.append(f"EXPECTED: {_show(f.get('expected', ''))}")
            L.append(f"GOT:      {_show(f.get('got', ''))}" + (f" ({f['note']})" if f.get("note") else ""))
            if f.get("why"):
                L += _wrap("WHY:      ", f["why"])
            L.append("")
        if L[-1] == "":
            L.pop()

    sugg, seen = [], set()
    for m in report["metrics"]:
        for s in m["suggestions"]:
            if s not in seen:
                seen.add(s)
                sugg.append(s)
    if sugg:
        L += ["", "--- Suggestions to raise the grade ---"] + [f"- {s}" for s in sugg]
    if report["flags"]:
        L += ["", "--- Flags (for instructor review, not a verdict) ---"]
        L += [f"- {f.get('kind')}: {f.get('detail', '')}" for f in report["flags"]]

    ul = report.get("usefulness_limitations")
    if ul:
        L += ["", "--- Usefulness & limitations of this evaluation ---", "Useful for:"]
        for i, u in enumerate(ul.get("usefulness", []), 1):
            L += _wrap(f"{i}. ", u["use_case"]) + _wrap("   Example: ", u["example"]) + _wrap("   Benefit: ", u["benefit"])
        L.append("Limits of this report:")
        for i, u in enumerate(ul.get("limitations", []), 1):
            L += _wrap(f"{i}. ", u["limitation"]) + _wrap("   Example: ", u["example"]) + _wrap("   Fix: ", u["mitigation"])
    L += ["", f"rules {report['rules_hash'][:19]}...  submission {report['submission_hash'][:19]}..."]
    return "\n".join(L) + "\n"


def write_reports(report: dict, out_dir, stem: str | None = None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = stem or Path(report["submission"]).stem
    jp, tp = out / f"{stem}.json", out / f"{stem}.txt"
    jp.write_text(report_to_json(report), encoding="utf-8")
    tp.write_text(render_text(report), encoding="utf-8")
    return jp, tp
