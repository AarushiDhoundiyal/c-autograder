"""modularity: does the program use helper functions besides main()?

params: expect_helpers (bool, default true), min_functions (default 2, counting main)
A helper only counts if it is defined AND called from another function, so a
dummy unused function cannot raise the score.
score = 1.0 if helpers not required; 0.3 if no called helper;
        else 0.3 + 0.7 * min(1, called_helpers / required_helpers)
"""
from agent import csource
from agent.registry import register, AnalyzerResult


@register("function_split", needs_execution=False)
class FunctionSplit:
    def run(self, ctx):
        info = csource.analyze(ctx.source_path.read_text(encoding="utf-8", errors="replace"))
        names = [f.name for f in info.functions]
        helpers = [f for f in info.functions if f.name != "main"]
        called = [f.name for f in helpers
                  if any(f.name in g.calls for g in info.functions if g.name != f.name)]
        required = max(1, int(ctx.params.get("min_functions", 2)) - 1)
        ev = {"functions_defined": len(names), "function_names": names,
              "helpers_defined": len(helpers), "helpers_called": called,
              "expected_helpers": required}
        if not ctx.params.get("expect_helpers", True):
            return AnalyzerResult(score=1.0, evidence=ev, feedback="helpers not required")
        if not called:
            only = "Only main() is defined." if not helpers else "Helper functions are defined but never called."
            return AnalyzerResult(score=0.3, evidence=ev, feedback=only,
                                  suggestions=["Move the core computation into its own function "
                                               "(for example int add(int a, int b)) and call it from main()."])
        score = 0.3 + 0.7 * min(1.0, len(called) / required)
        return AnalyzerResult(score=score, evidence=ev,
                              feedback=f"{len(called)} helper(s) used: {', '.join(called)}")
