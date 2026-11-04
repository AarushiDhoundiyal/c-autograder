"""Placeholders so a complete nine-metric rules file validates from day one.
Each reports status 'skipped' until its real analyzer module is added."""
from agent.registry import register, AnalyzerResult

# analyzer name -> (module that will replace it, needs the program to run?)
_PLANNED = {
    "io_tests": ("io_tests", True),
    "compiler_warnings": ("compiler_warnings", False),
    "static_analysis": ("static_analysis", False),
    "function_split": ("function_split", False),
    "sanitizer_run": ("sanitizer_run", True),
    "edge_case_runner": ("edge_case_runner", True),
    "complexity_estimator": ("complexity_estimator", True),
    "llm_review": ("llm_review", False),
    "similarity_flag": ("similarity_flag", False),
}


def _make(name, module, needs_exec):
    class Pending:
        def run(self, ctx):
            import analyzers
            why = analyzers.LOAD_ERRORS.get(module)
            msg = (f"analyzer module failed to load: {why}" if why
                   else f"analyzer '{name}' is not implemented yet")
            return AnalyzerResult(score=0.0, status="skipped", feedback=msg,
                                  evidence={"reason": "not_available"})
    Pending.__name__ = f"Pending_{name}"
    register(name, needs_execution=needs_exec)(Pending)


for _n, (_mod, _x) in _PLANNED.items():
    _make(_n, _mod, _x)
