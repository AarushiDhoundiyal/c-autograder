#!/usr/bin/env python3
"""Ask a local Ollama model to solve each problem several times and save the answers in
corpus/llm/<problem>/, so the originality check can flag submissions copied from an LLM.
Run it once when a problem is set up, not while grading. It needs Ollama running locally.

    python scripts/make_llm_corpus.py                      # every problem, 3 answers each
    python scripts/make_llm_corpus.py knapsack lis --count 5 --model llama3.1:8b

Each answer uses a different seed, so the answers differ but are repeatable. An answer that
does not compile is not saved. Existing files are kept unless --force is given."""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT = """Write a complete C program (C11) that solves the problem below. The program reads from
standard input and writes to standard output. Reply with the code only, in a single ```c block.

{spec}
"""


def problems_with_rules():
    return sorted(p.name for p in (ROOT / "problems").iterdir()
                  if (p / "spec.md").exists() and (ROOT / "rules" / f"{p.name}_full.json").exists())


def ask(host, model, prompt, seed, temperature, timeout):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": temperature, "seed": seed}}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response", "")


def extract_code(text):
    blocks = re.findall(r"```(?:c|C)?\s*\n(.*?)```", text, flags=re.S)
    code = max(blocks, key=len) if blocks else text
    return code.strip() + "\n" if "main" in code else None


def compiles(code):
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "answer.c"
        src.write_text(code)
        r = subprocess.run(["gcc", "-std=c11", "-fsyntax-only", str(src)], capture_output=True)
        return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("problems", nargs="*", help="problem folder names (default: all)")
    ap.add_argument("--count", type=int, default=3, help="answers per problem")
    ap.add_argument("--model", default="qwen2.5-coder:7b")
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    known = problems_with_rules()
    for name in args.problems:
        if name not in known:
            ap.error(f"unknown problem '{name}'; choose from {', '.join(known)}")
    tag = re.sub(r"[^A-Za-z0-9]+", "_", args.model).strip("_")
    for name in args.problems or known:
        spec = (ROOT / "problems" / name / "spec.md").read_text(encoding="utf-8")
        rules = json.loads((ROOT / "rules" / f"{name}_full.json").read_text(encoding="utf-8"))
        folder = ROOT / "corpus" / "llm" / rules["problem"]
        folder.mkdir(parents=True, exist_ok=True)
        saved = 0
        for seed in range(1, args.count + 1):
            out = folder / f"{tag}_seed{seed}.c"
            if out.exists() and not args.force:
                continue
            try:
                code = extract_code(ask(args.host, args.model, PROMPT.format(spec=spec), seed,
                                        args.temperature, args.timeout))
            except OSError as e:
                sys.exit(f"cannot reach Ollama at {args.host}: {e}")
            if code and compiles(code):
                out.write_text(code)
                saved += 1
            else:
                print(f"  {name}: answer for seed {seed} did not compile; skipped")
        print(f"{folder.relative_to(ROOT)}: {saved} answer(s) saved")


if __name__ == "__main__":
    main()
