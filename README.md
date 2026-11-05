# C AutoGrader

C AutoGrader grades C programming assignments on nine separate metrics instead of a single pass count. The weights, limits and thresholds come from a JSON rules file that an instructor can edit without touching the code. Every score is reported with evidence, and the same file graded under the same rules gives the same report on every run.

The system has two front ends that share one grading engine: a command-line program (`grade.py`) and a Django web application where students upload their work and instructors review the class.

## Contents

- [Features](#features)
- [The nine metrics](#the-nine-metrics)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Grading from the command line](#grading-from-the-command-line)
- [Web application](#web-application)
- [Running with Docker](#running-with-docker)
- [Rules files](#rules-files)
- [Adding a new problem](#adding-a-new-problem)
- [Adding a new analyzer](#adding-a-new-analyzer)
- [Reproducibility](#reproducibility)
- [Tests](#tests)
- [Security model](#security-model)
- [Known limitations](#known-limitations)
- [Project layout](#project-layout)
- [Environment variables](#environment-variables)
- [Authors](#authors)

## Features

- Nine metrics per submission, each with a score between 0 and 1, a comment, suggestions and evidence.
- Instructor-defined weights and parameters in a validated JSON file; all errors in the file are reported at once.
- A minimised failing input for logical errors, found by differential testing against a trusted reference solution.
- Time complexity measured from instruction counts (Valgrind callgrind), not wall-clock time.
- Memory errors detected with AddressSanitizer, UndefinedBehaviorSanitizer and LeakSanitizer.
- Copy detection against classmates' work, LLM-generated solutions and solutions collected online.
- Student code runs in a sandbox with CPU, memory, output and process limits, in an empty working directory.
- An integrity scan flags programs that try to open files, start processes or reach the network.
- Every report stores the SHA-256 hash of the submission and of the rules, and the versions of the tools used.
- A web application with uploads, status polling, a class table, CSV export, a versioned rule editor, bulk ZIP upload, regrading and a JSON API.

## The nine metrics

| Metric | Analyzer | What it measures | Score |
|---|---|---|---|
| correctness | `io_tests` | Output on the hidden tests, compared token by token | fraction of tests passed |
| syntax | `compiler_warnings` | gcc warnings (`-Werror` is removed so warnings are counted) | `max(0, 1 - 0.1 * warnings)`, 0 if it does not compile |
| structure | `static_analysis` | Cyclomatic complexity and function length (lizard), findings (cppcheck) | `0.35 * complexity + 0.30 * length + 0.35 * cppcheck` |
| modularity | `function_split` | Helper functions that are defined and actually called | `0.3 + 0.7 * min(1, called / required)` |
| logical | `edge_case_runner` | Agreement with the reference on named corner cases and seeded random cases | fraction of cases that agree |
| complexity | `complexity_estimator` | Growth of callgrind instruction counts, fitted to `a + b * n^k` | 1 within the required class, 0.5 one class slower, else 0 |
| memory_safety | `sanitizer_run` | ASan, UBSan and LSan findings on the hidden tests | `max(0, 1 - 0.34 * distinct findings)` |
| readability | `llm_review` | Source features (comments, names, layout, indentation, spacing) and an optional local LLM rating | `0.6 * features + 0.4 * LLM`, LLM capped at features + 0.3 |
| originality | `similarity_flag` | Winnowing fingerprints and Jaccard similarity against `corpus/` | 1 up to the threshold (0.85), then falls linearly to 0 |

The final grade is `100 * sum(weight_i * score_i)`, and the weights in a rules file must sum to 1.

## How it works

```
 browser / API ──> Django views ──> job worker ──> grade.py (child process) <── command line
                                                        │
                                                        v
                                     coordinator: first pass, dispatch, collation
                                                        │
              ┌──────────────┬──────────────┬───────────┴──┬──────────────┐
           rules.py      registry.py     sandbox.py     csource.py      report.py
                                                       integrity.py
                                                        │
                    source-only analyzers (parallel)  +  execution-based analyzers (one at a time)
```

1. **First pass.** The coordinator parses the source, compiles it with `-O2 -Wall -Wextra -std=c11` and runs it once on the smoke input from the rules file.
2. **Skip logic.** If the program does not compile, or does not finish the smoke run within the time limit, the four execution-based metrics are marked as skipped and the report is marked partial.
3. **Dispatch.** Analyzers that only read the source run in parallel threads. Analyzers that execute the program run one after another, so that time limits and instruction counts are not disturbed.
4. **Collation.** Scores are combined in the order of the rules file, flags are collected, the integrity scan is added, and the JSON and text reports are written.

An analyzer that crashes produces status `error` and score 0; the other metrics are still computed. The web application never imports the grading code: its worker starts `grade.py` as a separate process and reads back the JSON report, so student code never runs inside the web server.

## Requirements

- Linux (on Windows, use WSL or Docker)
- Python 3.12 or newer
- gcc with the sanitizer runtimes (`libasan`, `libubsan`)
- cppcheck (optional; without it the structure metric uses the other two parts only)
- Valgrind (optional; without it the complexity metric falls back to a low-confidence static estimate)
- Ollama with `qwen2.5-coder:7b` (optional; without it readability uses the source features only)

## Installation

```bash
git clone https://github.com/AarushiDhoundiyal/c-autograder.git
cd c-autograder

sudo apt-get update
sudo apt-get install -y gcc cppcheck valgrind

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To use the language-model part of the readability metric:

```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

## Grading from the command line

```bash
python grade.py samples/add_good.c --rules rules/add_full.json
```

| Option | Meaning |
|---|---|
| `source` | the student's `.c` file |
| `--rules` | the rules JSON file (required) |
| `--out-dir` | where to write `<name>.json` and `<name>.txt` (default `reports`) |
| `--workdir` | keep build files in this folder instead of a temporary one |
| `--quiet` | do not print the text report |

Part of the text report for `samples/add_good.c`:

```
===== Grading report for add_good.c =====
Overall grade: 99.27 / 100

Metric           Weight    Score   Points  Comment
correctness         20%     1.00    20/20  10/10 tests pass
syntax              10%     1.00    10/10  no warnings
structure           10%     1.00    10/10  2 function(s), max cyclomatic 2, 0 cppcheck finding(s)
modularity          10%     1.00    10/10  1 helper(s) used: add
logical             10%     1.00    10/10  17/17 edge cases handled
complexity          10%     1.00    10/10  Estimated O(1) (callgrind); required O(1)
memory_safety       10%     1.00    10/10  ASan/UBSan clean
readability         10%     0.93  9.27/10  Readability 9/10
originality         10%     1.00    10/10  max similarity 0.42 with llm/add_llm_example.c (not flagged)
```

For a failing submission, the report also has a "Where you failed" section that lists the input, the expected output, the actual output and a short explanation.

Other command-line tools:

```bash
# grade every sample and write reports/final/SUMMARY.txt
python scripts/run_samples.py

# find counter-examples for one submission and save them as test files
python -m agent.counter_tests samples/add_basic.c --rules rules/add_full.json --count 30

# callgrind and memcheck profile of one run
python -m agent.profiling samples/add_leak.c --input "7 5"
```

## Web application

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000. The `seed_demo` command creates both problems with their rules and two demo accounts: `teacher` / `teacher123` (instructor) and `student1` / `student123` (student). Change these before using the application with real users.

**Students** can upload a `.c` file, watch the run status, read the report, download it as text or JSON, and see their history. Copy-detection flags are hidden from students.

**Instructors** additionally get, for each problem:

- a class table with one column per metric and a CSV export (`/instructor/<problem>/`);
- the list of flagged submissions;
- a rule editor (`/instructor/<problem>/rules/`) that validates the JSON and saves a new version each time, so every submission keeps the rule version it was graded with;
- bulk upload of a ZIP archive of files named `<username>.c`;
- a regrade button that grades a submission again as a new run.

Uploads must be UTF-8 text files ending in `.c`, non-empty and at most 100 KB. A student can have at most three runs queued or running, and at most ten uploads are accepted per minute.

### JSON API

The API uses HTTP Basic authentication or an existing session.

```bash
curl -u student1:student123 -F problem=add -F file=@samples/add_good.c \
     http://127.0.0.1:8000/api/submissions/
# {"run_id": 1, "status": "queued"}

curl -u student1:student123 http://127.0.0.1:8000/api/runs/1/
# status, grade, partial flag, and the full report once the run is done
```

### Management commands

| Command | Purpose |
|---|---|
| `python manage.py seed_demo` | create the demo users, both problems and their rule sets (safe to run twice) |
| `python manage.py grade_pending` | re-queue runs that were interrupted by a server restart |
| `python manage.py export_corpus <problem>` | copy finished submissions into `corpus/peers/<problem>/` for copy detection |

## Running with Docker

The image installs gcc, cppcheck and Valgrind, runs student programs as the unprivileged user `nobody`, and makes the problem, rule and corpus folders unreadable to that user.

```bash
docker build -t c-autograder .

# command line, with no network access
docker run --rm --network none -v "$PWD/samples:/work" c-autograder \
    python grade.py /work/add_basic.c --rules rules/add_full.json

# web application
docker run -p 8000:8000 c-autograder sh -c \
    "python manage.py migrate && python manage.py seed_demo && python manage.py runserver 0.0.0.0:8000"
```

To make the web worker grade each job inside a fresh container, set `GRADER_USE_DOCKER=1`. The worker then runs `docker run --network none` with the image named in `GRADER_DOCKER_IMAGE`.

## Rules files

A rules file describes one problem. The example below is shortened from `rules/sum_array_full.json`.

```json
{
  "problem": "sum_array",
  "description": "Nine metrics with stricter structure limits.",
  "time_limit_s": 2,
  "memory_limit_mb": 128,
  "skipped_policy": "zero",
  "smoke_input": "3\n1 2 3\n",
  "metrics": [
    {"name": "correctness", "analyzer": "io_tests", "weight": 0.25,
     "params": {"testset_dir": "problems/sum_array/tests", "compare": "tokens"}},
    {"name": "complexity", "analyzer": "complexity_estimator", "weight": 0.15,
     "params": {"required": "O(n)", "generator": "array", "sizes": [1000, 2000, 4000, 8000]}}
  ]
}
```

| Key | Meaning |
|---|---|
| `problem` | problem name; also used to derive the seed for random test cases |
| `time_limit_s`, `memory_limit_mb` | limits for every run of the student program |
| `skipped_policy` | `zero` (a skipped metric adds nothing) or `renormalize` (remaining weights are rescaled to sum to 1) |
| `smoke_input` | input for the first-pass run |
| `metrics` | list of `{name, analyzer, weight, params}`; weights must sum to 1 |

The loader rejects unknown keys, non-positive limits, unknown analyzers, duplicate metric names, weights outside (0, 1] and weights that do not sum to 1, and it lists every error at once. Paths in `params` are resolved against the current folder, the folder of the rules file and the repository root.

Useful parameters:

| Analyzer | Parameters |
|---|---|
| `io_tests` | `testset_dir`, `compare` (`tokens`, `lines` or `exact`) |
| `compiler_warnings` | `flags`, `penalty_per_warning` |
| `static_analysis` | `max_cyclomatic` (default 8), `max_function_length` (default 40) |
| `function_split` | `expect_helpers`, `min_functions` |
| `edge_case_runner` | `reference`, `edge_cases_file`, `cases` (groups to use, such as `negatives`, `zero`, `int_overflow`, `whitespace`, `crlf`, `no_trailing_newline`, `leading_zeros`, `plus_sign`, `random`), `random_count`, `minimise_drop_tokens` |
| `complexity_estimator` | `required` (`O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n^2)`, `O(n^3)`), `generator` (`scalar`, `single_n`, `array`), `sizes`, `method` (`auto`, `callgrind`, `static`), `profile` |
| `sanitizer_run` | `testset_dir`, `flags` |
| `llm_review` | `backend` (`ollama` or `none`), `model`, `temperature`, `seed`, `cache_dir`, `llm_share`, `llm_max_uplift`, `require_llm`, `host` |
| `similarity_flag` | `corpus_dir`, `flag_threshold`, `min_tokens`, `penalize` |

For the complexity metric, choose sizes large enough that the program's work is well above its start-up cost (about 150,000 instructions). For an O(n) problem, `[1000, 2000, 4000, 8000]` works well; for O(1), the default `[1, 10, 100]` is enough.

## Adding a new problem

1. Create `problems/<name>/spec.md` with the problem statement. Write down any decision that affects the expected output, such as how integer overflow is handled.
2. Add a trusted reference solution, `problems/<name>/reference.c`.
3. Add hidden tests as numbered pairs `tests/001.in` and `tests/001.out`, `tests/002.in` and `tests/002.out`, and so on. Compute expected outputs independently of any student program; `scripts/make_problem_tests.py` shows how this is done for the two included problems.
4. Add `problems/<name>/edge_cases.json` with named groups of inputs and an optional `random` section. Expected outputs for these cases always come from the reference solution.
5. Copy one of the files in `rules/`, change the paths and weights, and grade a few sample programs with it.

## Adding a new analyzer

1. Create `analyzers/<module>.py`:

   ```python
   from agent.registry import AnalyzerResult, register


   @register("my_metric", needs_execution=False)
   class MyMetric:
       def run(self, ctx):
           source = ctx.source_path.read_text(encoding="utf-8", errors="replace")
           return AnalyzerResult(score=1.0, evidence={}, feedback="ok", suggestions=[], flags=[])
   ```

2. Add the module name to `MODULES` in `analyzers/__init__.py`.
3. Add a metric that uses it to a rules file.

The context `ctx` gives `source_path`, `binary_path`, `workdir`, `params`, `sandbox`, `first_pass` and `resolve(path)` for paths written in the rules file. Set `needs_execution=True` if the analyzer runs the student program; it is then skipped when the program does not compile or loops forever. Failing inputs placed in `evidence["failing"]` as a list of `{"test", "input", "expected", "got", "note", "why"}` are printed in the "Where you failed" section of the report.

## Reproducibility

The same submission graded under the same rules on the same toolchain gives a byte-identical report:

- reports contain no timestamps, and metrics appear in rules-file order;
- random test cases use a seed derived from the rules hash and the problem name;
- complexity uses instruction counts, not time;
- fingerprints use BLAKE2b instead of Python's randomised `hash()`;
- the language model runs at temperature 0 with a fixed seed, and its answers are cached.

```bash
python scripts/repro_check.py --runs 10 samples/add_good.c samples/add_leak.c samples/add_crash.c
```

Grades can differ between machines with different tools. For example, a machine without cppcheck computes the structure metric from two parts instead of three. Each report therefore records the versions of gcc, cppcheck, lizard, Valgrind and Python, and notes any missing tool. For grades that must not depend on whether Ollama is installed, set `"backend": "none"` in the readability parameters.

## Tests

```bash
python -m pytest -q tests
```

The suite covers the rules loader, the sandbox, the C-source inspector, the coordinator, every analyzer, a three-run determinism test over all nine metrics with a fake language-model server, the security fixes (including the original test-file exploit), and the Django views, API and permissions. Tests that need Valgrind are skipped when it is not installed, and a few sandbox tests are skipped or run depending on whether the grader runs as root.

The GitHub Actions workflow in `.github/workflows/ci.yml` installs the tools, runs the tests, repeats the 10-run reproducibility check and uploads the sample reports on every push.

## Security model

Student code is untrusted. The grader protects itself as follows:

- every compiler and student process runs with limits on CPU time, address space, output size (1 MiB) and process count, with core dumps disabled, in its own process group that is killed on timeout;
- every student run starts in a fresh, empty temporary folder, so relative paths to the hidden tests do not resolve;
- when the grader runs as root with `AUTOGRADER_DROP_PRIVILEGES=1` (the default in the Docker image), student programs run as `nobody`;
- an integrity scan looks for file, process, network and dynamic-loading calls, test-file paths and includes of outside files, and raises a `suspicious_code` flag; it never changes the grade, because honest programs sometimes open files;
- student code is passed to the language model as marked data; text addressed to the reviewer disables the model score and raises a `prompt_injection_suspected` flag, and the model can lift the readability score by a bounded amount only.

`samples/add_cheat_reads_tests.c` is a program that tries to copy answers from the hidden test files. It is kept as a regression sample, and `tests/test_hardening.py` checks that it scores 0 on correctness and is flagged.

What is **not** covered:

- without root or Docker, a student program can read any file that the grader's user can read through an absolute path;
- the compiler is not isolated, so `#include "/some/file"` can pull a file into an error message (the integrity scan flags such includes);
- the sandbox does not block the network by itself; use `docker run --network none`;
- the prompt-injection phrase list can be evaded; the cap on the model's influence is the main protection.

## Known limitations

- The reference solution defines what is correct. If it, or the specification behind it, is wrong, correct students are marked wrong.
- Without Valgrind, the complexity estimate comes from loop nesting and cannot tell O(log n) from O(n). Such results are marked low confidence and should be reviewed by a person.
- Copy detection misses heavily restructured code and sources that are not in the corpus. Very short programs look alike, so programs below `min_tokens` are never flagged. A flag is a request for human review, not a verdict.
- The readability score differs between machines with and without Ollama.
- The web job queue lives in memory with a single worker thread. This is enough for a class, but not for a large course. Run `grade_pending` after a restart.
- Only Linux is fully supported.

## Project layout

```
c-autograder/
├── grade.py                 command-line entry point
├── manage.py                Django entry point
├── agent/                   grading engine
│   ├── coordinator.py       first pass, dispatch, collation
│   ├── rules.py             rules loading, validation and hashing
│   ├── registry.py          analyzer interface and registry
│   ├── sandbox.py           compile and run under limits
│   ├── csource.py           comment-proof C inspection (tree-sitter with a fallback scanner)
│   ├── integrity.py         scan for suspicious calls and paths
│   ├── testset.py           discovery of NNN.in / NNN.out test pairs
│   ├── counter_tests.py     differential testing and input minimiser
│   ├── profiling.py         callgrind and memcheck helpers
│   ├── similarity.py        token normalisation and winnowing
│   └── report.py            JSON and text reports
├── analyzers/               the nine metric analyzers
├── rules/                   rules files (add_full, add_core, sum_array_full)
├── problems/                specification, reference solution, hidden tests and edge cases per problem
├── samples/                 example submissions, each with a deliberate fault
├── corpus/                  known solutions for copy detection (peers/, llm/, online/)
├── grader/                  Django app: models, views, forms, jobs, API, templates
├── autograder_web/          Django project settings and URLs
├── scripts/                 test generation, sample runs, reproducibility check
├── tests/                   pytest suite
├── docs/                    usefulness and limitation examples included in every report
├── Dockerfile
└── .github/workflows/ci.yml
```

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | development value | secret key; set a real one outside development |
| `DJANGO_DEBUG` | `1` | set to `0` outside development |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver` | comma-separated host names |
| `AUTOGRADER_DB` | `db.sqlite3` | path of the SQLite database |
| `AUTOGRADER_MEDIA` | `media/` | folder for uploaded files |
| `GRADER_SYNC` | `0` | `1` grades inside the request (for tests and debugging) |
| `GRADER_USE_DOCKER` | `0` | `1` grades each job in `docker run --network none` |
| `GRADER_DOCKER_IMAGE` | `c-autograder` | image used when `GRADER_USE_DOCKER=1` |
| `AUTOGRADER_DROP_PRIVILEGES` | unset | `1` runs student programs as an unprivileged user when the grader is root |
| `AUTOGRADER_RUN_UID` | `65534` | user id for student programs when privileges are dropped |
| `AUTOGRADER_NO_TREE_SITTER` | unset | `1` forces the fallback C scanner |

## Authors

- Aarushi Dhoundiyal, Department of Computer Science and Engineering, IIT Patna
- Ayushi Singh, Department of Computer Science and Engineering, IIT Patna
- Nabam Sital, Department of Computer Science and Engineering, IIT Patna
