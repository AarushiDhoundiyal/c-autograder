# Security patch: hidden tests, integrity scan, LLM prompt injection

Unzip over the repo (it replaces 5 files and adds 4). Then `python -m pytest -q tests` (121+ pass).

## The problem that was found
A student program could read the grader's hidden tests. A C program that opened
`problems/add/tests/NNN.out` scored 10/10 on correctness with no flag. Student code
ran in the grader's own working directory, and in the Docker image the tests were readable
by the same user. The LLM review also pasted raw student code into its prompt.

## What changed
| File | Change |
|---|---|
| agent/sandbox.py | Student runs start in a fresh EMPTY directory. With `AUTOGRADER_DROP_PRIVILEGES=1` and a root grader they run as `nobody` (also makes the fork-bomb limit work as root). `run(..., trusted=True)` for the grader's own tools. |
| agent/integrity.py (new) | Scans the source for file / process / network calls, path strings such as "tests/001.out", and `#include "../x"`. Raises a `suspicious_code` flag. NEVER changes the grade. Ignores comments and the student's own helper functions. |
| agent/coordinator.py | Runs the scan; records `first_pass.isolation`; reports when a privilege drop was requested but the grader is not root. |
| analyzers/static_analysis.py | cppcheck is marked `trusted` (it is the grader's tool, not student code). |
| analyzers/llm_review.py | Code goes in `<student_code>` tags with an "untrusted data" rule; text aimed at the reviewer disables the LLM score and raises `prompt_injection_suspected`; the model can lift the score at most `llm_max_uplift` (0.3) above the deterministic checks. |
| Dockerfile | Grader runs as root inside the container, `AUTOGRADER_DROP_PRIVILEGES=1`, problem/rule folders chmod 0700. |
| samples/add_cheat_reads_tests.c (new) | The cheating program, kept as a regression sample. |
| samples/sum_array_quadratic.c | Replaced: the old one was really O(n). Now correct but O(n^2), so it loses the complexity points. |
| tests/test_hardening.py (new) | 19 tests including the original exploit. |

## Verified
* Exploit through a relative path: correctness 10/10 -> 0/10, flagged.
* Exploit through an ABSOLUTE path: blocked only with the privilege drop (root-only test, control proves the file was readable to root).
* Grades are identical with and without the privilege drop on all 11 samples, all nine metrics.
* Full suite: 121+ passed.

## What it does NOT solve (say so in your report)
* Without root (or Docker) there is no protection against absolute paths: student code can read anything your own user can read. The report then says so in `first_pass.notes`.
* Network is not blocked by the sandbox itself. Use `docker run --network none`.
* The Dockerfile change and `GRADER_USE_DOCKER` were NOT run: no Docker was available here. Build the image once and run
  `python scripts/run_samples.py` inside it before relying on it.
* gcc still runs as the grader's user: `#include "/some/file"` can pull a file into compiler error messages. The scan flags such includes but compilation is not isolated.
* The Django web app runs as root inside that container if you use the Dockerfile as is; only the student programs are unprivileged.
* The injection detector is a phrase list. A cleverly worded attempt can slip past it; the uplift cap and the 40% LLM share limit the damage.
