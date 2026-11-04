"""The coordinating agent: first pass, dispatch, collation.

Decision logic
  compile fails           -> skip execution-based analyzers, grade source-only ones
  smoke run times out     -> flag suspected_infinite_loop, same skipping
  analyzer raises         -> that metric becomes status 'error' (score 0); the rest still run
  source-only analyzers   -> parallel threads;  execution-based analyzers -> one at a time
Results are always assembled in rules-file order, so reports are reproducible.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path

from agent import REPO_ROOT, csource, integrity, registry, sandbox
from agent.registry import AnalyzerContext, AnalyzerResult
from agent.rules import Rules, load_rules
from agent.report import tool_versions

FIRST_PASS_FLAGS = ["-O2", "-Wall", "-Wextra", "-std=c11"]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _first_pass(source: Path, rules: Rules, sb, workdir: Path):
    """Cheap sanity sweep. Returns (report dict, binary path or None)."""
    text = source.read_text(encoding="utf-8", errors="replace")
    info = csource.analyze(text)
    fp = {"compiled": False, "compile_warnings": 0, "compile_errors": [],
          "smoke_ok": False, "smoke_outcome": "NOT_RUN",
          "suspected_infinite_loop": False,
          "static_sanity": {"has_main": info.has_main, "has_reader": info.has_reader,
                            "has_writer": info.has_writer, "main_returns": info.main_returns,
                            "ok": info.sanity_ok},
          "notes": info.sanity_notes(), "parser": info.backend,
          "isolation": {"private_empty_cwd": True, "privilege_drop": sb.privilege_drop_active}}
    if sb.drop_requested and not sb.privilege_drop_active:
        fp["notes"].append("privilege drop was requested but the grader is not root: "
                           "student code can read files the grader's user can read")
    binary = workdir / "submission.bin"
    comp = sb.compile(source, binary, FIRST_PASS_FLAGS, cwd=source.parent)
    fp["compile_warnings"] = len(comp.warnings)
    if not comp.ok:
        fp["compile_errors"] = comp.errors[:10]
        fp["notes"].append("does not compile: execution-based metrics are skipped")
        return fp, None
    fp["compiled"] = True
    smoke = sb.run([binary], stdin=rules.smoke_input)
    fp["smoke_outcome"] = smoke.outcome
    fp["smoke_ok"] = smoke.ok
    if smoke.outcome == sandbox.TIMEOUT:
        fp["suspected_infinite_loop"] = True
        fp["notes"].append("smoke run timed out: execution-based metrics are skipped")
    return fp, binary


def _clean(text: str, workdir: Path) -> str:
    return text.replace(str(workdir), "<work>")[:200]


def _run_analyzer(spec, skip_reason, make_ctx, workdir) -> AnalyzerResult:
    entry = registry.get(spec.analyzer)
    if skip_reason and entry.needs_execution:
        return AnalyzerResult(score=0.0, status="skipped", feedback=f"Skipped: {skip_reason}.",
                              evidence={"reason": skip_reason})
    try:
        res = entry.cls().run(make_ctx(spec))
        if not isinstance(res, AnalyzerResult):
            raise TypeError("analyzer did not return an AnalyzerResult")
        res.score = max(0.0, min(1.0, float(res.score)))
        return res
    except Exception as e:  # noqa: BLE001 - isolate analyzer failures
        return AnalyzerResult(score=0.0, status="error",
                              feedback=f"Analyzer crashed: {type(e).__name__}: {_clean(str(e), workdir)}",
                              evidence={"error": type(e).__name__})


def _load_usefulness():
    p = REPO_ROOT / "docs" / "usefulness_limitations.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def grade_submission(source_path, rules, workdir=None, max_workers: int = 4) -> dict:
    """Grade one C file under a rules file (path or Rules). Returns the report dict."""
    rules = rules if isinstance(rules, Rules) else load_rules(rules)
    source = Path(source_path).resolve()
    sb = sandbox.Sandbox(rules.time_limit_s, rules.memory_limit_mb)
    base_dirs, seen = [], set()
    for d in (Path.cwd(), rules.base_dir, REPO_ROOT):
        if d not in seen:
            seen.add(d)
            base_dirs.append(d)

    with ExitStack() as stack:
        if workdir is None:
            work = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="autograder_")))
        else:
            work = Path(workdir)
            work.mkdir(parents=True, exist_ok=True)

        fp, binary = _first_pass(source, rules, sb, work)
        skip_reason = None
        if not fp["compiled"]:
            skip_reason = "the program does not compile"
        elif fp["suspected_infinite_loop"]:
            skip_reason = "suspected infinite loop"

        def make_ctx(spec):
            return AnalyzerContext(source_path=source, binary_path=binary, workdir=work,
                                   params=spec.params, rules=rules, sandbox=sb,
                                   first_pass=fp, base_dirs=base_dirs)

        results: dict[str, AnalyzerResult] = {}
        src_only = [m for m in rules.metrics if not registry.get(m.analyzer).needs_execution]
        exec_based = [m for m in rules.metrics if registry.get(m.analyzer).needs_execution]
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futs = {m.name: pool.submit(_run_analyzer, m, skip_reason, make_ctx, work)
                    for m in src_only}
            for name, fut in futs.items():
                results[name] = fut.result()
        for m in exec_based:                       # sequential: parallel load skews measurements
            results[m.name] = _run_analyzer(m, skip_reason, make_ctx, work)

    # ---- collation, always in rules-file order -------------------------------
    metrics, flags, total, active_weight = [], [], 0.0, 0.0
    for m in rules.metrics:
        r = results[m.name]
        contribution = round(r.score * m.weight * 100 + 0.0, 2) if r.status == "ok" else 0.0
        if r.status != "skipped":
            active_weight += m.weight
        total += contribution
        flags.extend(r.flags)
        metrics.append({"name": m.name, "analyzer": m.analyzer, "status": r.status,
                        "score": round(r.score, 4), "weight": m.weight,
                        "contribution": contribution, "evidence": r.evidence,
                        "feedback": r.feedback, "suggestions": list(r.suggestions)})
    any_skipped = any(x["status"] == "skipped" for x in metrics)
    if rules.skipped_policy == "renormalize" and any_skipped:
        total = total / active_weight if active_weight > 0 else 0.0
    if fp["suspected_infinite_loop"]:
        flags.insert(0, {"kind": "suspected_infinite_loop",
                         "detail": "the program did not finish the smoke run within the time limit"})

    scan_flag = integrity.flag_from(integrity.scan(source.read_text(encoding="utf-8", errors="replace")))
    if scan_flag:
        flags.append(scan_flag)
    report = {"submission": source.name, "submission_hash": _sha256(source),
              "rules_hash": rules.hash, "problem": rules.problem,
              "grade": round(total + 0.0, 2),
              "partial": any(x["status"] != "ok" for x in metrics),
              "first_pass": fp, "metrics": metrics, "flags": flags,
              "tool_versions": tool_versions()}
    ul = _load_usefulness()
    if ul:
        report["usefulness_limitations"] = ul
    return report
