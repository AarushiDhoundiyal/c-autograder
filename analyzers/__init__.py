"""Analyzer package. Importing it registers every analyzer that exists.

Each analyzer is a module file in this package (io_tests.py, compiler_warnings.py,
...). Modules are imported in the order below, so a real analyzer replaces the
placeholder registered by pending.py. A module that is missing is skipped
silently; a module that crashes on import is recorded in LOAD_ERRORS
and its placeholder stays active, so one broken file never stops the agent.
"""
import importlib

LOAD_ERRORS: dict = {}

MODULES = ["pending", "io_tests", "compiler_warnings", "static_analysis",
           "function_split", "sanitizer_run", "edge_case_runner",
           "complexity_estimator", "llm_review", "similarity_flag"]

for _m in MODULES:
    _full = f"{__name__}.{_m}"
    try:
        importlib.import_module(_full)
    except ModuleNotFoundError as _e:
        if _e.name != _full:                 # a dependency is missing, not the module
            LOAD_ERRORS[_m] = f"{type(_e).__name__}: {_e}"
    except Exception as _e:                  # noqa: BLE001
        LOAD_ERRORS[_m] = f"{type(_e).__name__}: {_e}"
