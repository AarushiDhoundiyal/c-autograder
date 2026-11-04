"""syntax: compile with the rule's flags and count warnings.

params: flags (default "-Wall -Wextra -std=c11"), penalty_per_warning (default 0.1)
-Werror is removed (and recorded) so warnings are counted, not fatal. If the flags set no
-O level, -O2 is added (as in the coordinator's first pass) because gcc reports some
warnings only when optimising.
score = 0 if it does not compile, else max(0, 1 - penalty * warnings).
"""
import re
import shlex
from collections import Counter

from agent.registry import register, AnalyzerResult

ADVICE = {
    "unused-variable": "Remove variables you never use.",
    "unused-parameter": "Remove or use the unused function parameter.",
    "unused-but-set-variable": "Remove variables that are assigned but never read.",
    "unused-result": "Check the return value of scanf/fread (it reports whether input was read).",
    "implicit-function-declaration": "Include the header that declares the function you call.",
    "format": "Make the printf/scanf format specifier match the argument type.",
    "sign-compare": "Do not compare signed and unsigned values directly; cast deliberately.",
    "uninitialized": "Give every variable a value before it is read.",
    "maybe-uninitialized": "Give every variable a value before it is read.",
    "return-type": "Make sure every non-void function returns a value.",
}
_FLAG = re.compile(r"\[-W([\w-]+)")


@register("compiler_warnings", needs_execution=False)
class CompilerWarnings:
    def run(self, ctx):
        raw = ctx.params.get("flags", "-Wall -Wextra -std=c11")
        flags = shlex.split(raw) if isinstance(raw, str) else list(raw)
        werror = "-Werror" in flags
        flags = [f for f in flags if f != "-Werror"]
        added_o2 = not any(f.startswith("-O") for f in flags)
        if added_o2:                  # some warnings (e.g. unused-result) only appear when optimising
            flags.append("-O2")
        penalty = float(ctx.params.get("penalty_per_warning", 0.1))
        comp = ctx.sandbox.compile(ctx.source_path, ctx.workdir / "warnings.bin", flags,
                                   cwd=ctx.source_path.parent)
        if not comp.ok:
            first = comp.errors[0] if comp.errors else "compilation failed"
            return AnalyzerResult(score=0.0, feedback=f"Does not compile: {first}",
                                  evidence={"compiled": False, "errors": comp.errors[:5]},
                                  suggestions=["Fix the compile errors first; nothing else can be judged until it builds."])
        by_flag = Counter((_FLAG.search(w).group(1) if _FLAG.search(w) else "other")
                          for w in comp.warnings)
        n = len(comp.warnings)
        sugg = [ADVICE.get(f, f"Fix the -W{f} warning.") for f in sorted(by_flag)]
        fb = "no warnings" if n == 0 else ", ".join(f"-W{f} x{c}" for f, c in sorted(by_flag.items()))
        return AnalyzerResult(score=max(0.0, 1.0 - penalty * n),
                              evidence={"compiled": True, "flags": " ".join(flags),
                                        "werror_removed": werror, "added_O2": added_o2, "warnings": n,
                                        "by_flag": dict(sorted(by_flag.items())),
                                        "first_warnings": comp.warnings[:5]},
                              feedback=fb, suggestions=sugg)
