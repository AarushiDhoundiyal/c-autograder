"""structure: cyclomatic complexity, function length and cppcheck findings.

params: max_cyclomatic (default 8), max_function_length (default 40)
score = 0.35 * share of functions within the cyclomatic limit
      + 0.30 * share within the length limit
      + 0.35 * max(0, 1 - 0.25 * cppcheck findings)
If cppcheck is not installed the weights become 0.5 / 0.5 over the first two.
lizard is used when installed; otherwise an equivalent built-in count is used.
"""
import re
import shutil

from agent import csource
from agent.registry import register, AnalyzerResult

_DECISION = re.compile(r"\b(?:if|for|while|case)\b|&&|\|\||\?")
_FINDING = re.compile(r"^(\d+):(\w+):([\w.-]+):(.*)$")
_IGNORED_IDS = {"missingIncludeSystem", "missingInclude", "checkersReport",
                "normalCheckLevelMaxBranches", "unmatchedSuppression"}


def _measure_functions(ctx):
    """[{name, cyclomatic, length}] sorted by position, plus the tool used."""
    try:
        import lizard
        res = lizard.analyze_file(str(ctx.source_path))
        fl = sorted(res.function_list, key=lambda f: f.start_line)
        return ([{"name": f.name, "cyclomatic": f.cyclomatic_complexity,
                  "length": f.end_line - f.start_line + 1} for f in fl], "lizard")
    except ImportError:
        info = csource.analyze(ctx.source_path.read_text(encoding="utf-8", errors="replace"))
        return ([{"name": f.name, "cyclomatic": 1 + len(_DECISION.findall(f.body)),
                  "length": f.length} for f in info.functions], "builtin")


def _cppcheck(ctx):
    """Return list of findings, or None when cppcheck is unavailable."""
    if shutil.which("cppcheck") is None:
        return None
    r = ctx.sandbox.run(
        ["cppcheck", "--enable=warning,style,performance,portability", "--quiet",
         "--template={line}:{severity}:{id}:{message}", ctx.source_path.name],
        time_limit_s=60, memory_limit_mb=None, nproc=None, cwd=ctx.source_path.parent,
        trusted=True)
    out = []
    for line in r.stderr.splitlines():
        m = _FINDING.match(line.strip())
        if m and m.group(3) not in _IGNORED_IDS:
            out.append({"line": int(m.group(1)), "severity": m.group(2),
                        "id": m.group(3), "message": m.group(4).strip()})
    return out


@register("static_analysis", needs_execution=False)
class StaticAnalysis:
    def run(self, ctx):
        max_cc = int(ctx.params.get("max_cyclomatic", 8))
        max_len = int(ctx.params.get("max_function_length", 40))
        funcs, tool = _measure_functions(ctx)
        findings = _cppcheck(ctx)
        sugg = []
        if funcs:
            ok_cc = sum(f["cyclomatic"] <= max_cc for f in funcs) / len(funcs)
            ok_len = sum(f["length"] <= max_len for f in funcs) / len(funcs)
        else:
            ok_cc = ok_len = 0.0
            sugg.append("No functions were detected; define main() and helper functions.")
        for f in funcs:
            if f["cyclomatic"] > max_cc:
                sugg.append(f"Split {f['name']}(): cyclomatic complexity {f['cyclomatic']} exceeds {max_cc}.")
            if f["length"] > max_len:
                sugg.append(f"Shorten {f['name']}(): {f['length']} lines exceeds {max_len}.")
        if findings is None:
            score = 0.5 * ok_cc + 0.5 * ok_len
            cpp_note = "cppcheck not installed"
        else:
            score = 0.35 * ok_cc + 0.30 * ok_len + 0.35 * max(0.0, 1 - 0.25 * len(findings))
            cpp_note = f"{len(findings)} cppcheck finding(s)"
            for f in findings[:5]:
                sugg.append(f"Line {f['line']}: {f['message']} ({f['id']})")
        fb = (f"{len(funcs)} function(s), max cyclomatic "
              f"{max((f['cyclomatic'] for f in funcs), default=0)}, {cpp_note}")
        return AnalyzerResult(score=score, feedback=fb, suggestions=sugg,
                              evidence={"measured_with": tool, "functions": funcs,
                                        "limits": {"max_cyclomatic": max_cc, "max_function_length": max_len},
                                        "cppcheck": findings if findings is not None else "not installed"})
