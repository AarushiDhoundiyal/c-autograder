# C AutoGrader

## Project Goal

C AutoGrader is a rule-driven evaluator for student C programs. It aims to assess submissions using configurable grading rules, automated tests, and clear feedback.

## Core Contract

**Same submission + same rules = same grade.**

Given the same C source file and the same grading rules, the evaluator should produce the same result under the same execution environment.

## Planned Features

- Compile student C programs and report compilation errors.
- Test program outputs against expected results.
- Calculate grades using configurable rules and weights.
- Generate JSON and human-readable reports.
- Provide evidence and feedback to help explain the grade.

## Technology

- Python
- GCC
- JSON-based grading configuration

## Project Status

**Status: In progress.**

The project is being developed incrementally. Features will be added and tested throughout development.