# Part 1 of 4: engine core

Unzip into the root of your c-autograder repo (your README.md, problems/ and
LICENSE stay untouched). Then:

    pip install -r requirements.txt        # after merging requirements-part1.txt
    python -m pytest -q tests              # 29 pass, 1 skipped when run as root
    python grade.py some.c --rules rules/add_full.json

Until Parts 2-4 arrive every analyzer is a placeholder that reports "skipped",
so the grade is 0 and PARTIAL. That is expected.

## What is in Part 1
| File | Purpose | Suggested owner |
|---|---|---|
| agent/rules.py, rules/*.json | validated, hashed, editable rules | Aarushi |
| agent/registry.py | analyzer interface + registry | Aarushi |
| agent/sandbox.py | compile/run under time, memory, output limits | Aarushi |
| agent/coordinator.py | first pass, skip logic, dispatch, collation | Aarushi |
| agent/report.py, grade.py | JSON/text reports, CLI | Aarushi |
| agent/csource.py | comment-proof C inspection (tree-sitter + fallback) | Ayushi |
| analyzers/pending.py, analyzers/__init__.py | placeholders + auto-loader | Aarushi |
| tests/ | rules, sandbox, csource, coordinator, 10-run determinism | Nabam |

## Contract the later parts follow (do not change)
* A new analyzer is a file `analyzers/<module>.py`, listed in `MODULES` of
  analyzers/__init__.py (the names for Parts 2-4 are already listed):
  io_tests, compiler_warnings, static_analysis, function_split, sanitizer_run,
  edge_case_runner, complexity_estimator, llm_review, similarity_flag.
* It registers with `@register("<analyzer name>", needs_execution=...)` and
  implements `run(ctx) -> AnalyzerResult(score 0..1, evidence, feedback, suggestions, flags)`.
* `ctx` gives source_path, binary_path, workdir, params, sandbox, first_pass,
  and `ctx.resolve(path)` for paths written in the rules file.
* Failing inputs go in `evidence["failing"] = [{"test","input","expected","got","note","why"}]`;
  the text report prints them under "Where you failed".
* Copy flags go in `AnalyzerResult.flags = [{"kind": "similarity", "detail": "..."}]`.
* Rules param names are already fixed in rules/add_full.json.
* Paths in rules (problems/add/tests, ...) are resolved against the current
  directory, the rules file's directory, then the repo root. Adjust
  `testset_dir` if your tests folder in problems/add is named differently.

## Notes
* Linux/macOS only (resource limits). On Windows use WSL or the Docker image (Part 4).
* Run as a normal user for full process-count protection (RLIMIT_NPROC is ignored for root).
