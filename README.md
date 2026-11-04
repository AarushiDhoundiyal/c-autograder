# C AutoGrader

A rule-driven, reproducible system that grades C programs on nine metrics: correctness, syntax,
structure, modularity, logical edge cases, time complexity, memory safety, readability and originality.
Every lost mark comes with evidence, the instructor controls the weights in a JSON file, and the same
file graded under the same rules always gives the same grade.

Course: CS5103 Computing Lab - 1, Department of Computer Science and Engineering, IIT Patna.

## Quick start (Linux, macOS or WSL)

```bash
sudo apt-get install -y gcc cppcheck valgrind      # system tools
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests                          # run the test suite
python grade.py samples/add_good.c --rules rules/add_full.json
```

Web app:

```bash
python manage.py migrate && python manage.py seed_demo && python manage.py runserver
# student1 / student123, teacher / teacher123  ->  http://127.0.0.1:8000
```

An optional local language model improves the readability score: `ollama pull qwen2.5-coder:7b`.

## Repository layout and ownership

The repository is built from three parts. Each file belongs to exactly one part, so the parts never
edit the same file. Parts must be merged in order: Part 1, then Part 2, then Part 3.

| Part | Scope | Main folders and files |
|---|---|---|
| 1. Core engine and shared data | Rules, registry, sandbox, coordinator, reports, integrity scan, problems, samples, rules files, CI | `agent/` (core files), `grade.py`, `analyzers/__init__.py`, `analyzers/pending.py`, `rules/`, `problems/`, `samples/`, `scripts/`, `.github/` |
| 2. Nine analyzers | The nine metric plug-ins and their helper modules | `analyzers/*.py` (nine metrics), `agent/counter_tests.py`, `agent/profiling.py`, `agent/similarity.py`, `corpus/` |
| 3. Web app, security tests and delivery | Django web application, Docker, integration and security tests | `grader/`, `autograder_web/`, `manage.py`, `Dockerfile`, `tests/test_part4.py`, `tests/test_hardening.py` |

Owners: Part 1 [name], Part 2 [name], Part 3 [name].

## How the parts connect

- Every analyzer follows the contract in `agent/registry.py` and registers itself by name.
- `analyzers/__init__.py` imports each analyzer module that exists. A missing module is skipped and its
  placeholder (`analyzers/pending.py`) stays active, so the project runs after each part is merged.
- The web app never imports grading code. `grader/jobs.py` starts `grade.py` as a child process.

The design of each part is described in the project report.
