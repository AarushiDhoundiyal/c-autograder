"""originality: copy detection by normalised winnowing similarity.

params: corpus_dir ("corpus/"), corpus_problem (default: the rules file's "problem"),
        flag_threshold (0.85), min_tokens (30), k (5), window (4),
        penalize (true: lower the score when above the threshold)
Corpus layout: corpus/<kind>/<problem>/*.c, where kind is peers (earlier batches),
llm (LLM-generated solutions) or online (collected online solutions), and problem is
the "problem" name of the rules file. A submission is compared only with the folders
of its own problem; loose .c files directly in corpus/ or corpus/<kind>/ are compared
with every problem.
Classmates: when the grader is given a peers folder (grade.py --peers, or the web
worker, which passes the latest submission of every other student for the same
problem), every .c file in it is compared as well, except the submission itself.

A match above the threshold becomes a FLAG for human review, never a verdict.
Programs shorter than min_tokens are never flagged: tiny programs look alike.
Score: 1.0 below the threshold, falling linearly to 0 as similarity approaches 1.0.
"""
from pathlib import Path

from agent import csource
from agent.registry import register, AnalyzerResult
from agent.similarity import normalise_tokens, fingerprints, jaccard

KIND = {"llm": "llm_copy", "online": "online_copy"}


def _kind(rel: Path) -> str:
    return KIND.get(rel.parts[0], "similarity") if len(rel.parts) > 1 else "similarity"


def corpus_files(corpus: Path, problem: str) -> list:
    """The corpus files that apply to `problem`, as (path, name shown in the report, flag kind)."""
    if not corpus.is_dir():
        return []
    out = []
    for f in sorted(corpus.rglob("*.c")):
        rel = f.relative_to(corpus)
        if len(rel.parts) <= 2 or rel.parts[1] == problem:
            out.append((f, rel.as_posix(), _kind(rel)))
    return out


def peer_files(peers: Path, me: Path) -> list:
    if not peers or not peers.is_dir():
        return []
    return [(f, "peers/" + f.relative_to(peers).as_posix(), "similarity")
            for f in sorted(peers.rglob("*.c")) if f.resolve() != me]


def _style_hint(src: str):
    stripped = csource.blank_comments_and_strings(src)
    code = [l for l in stripped.splitlines() if l.strip()]
    raw = [l for l in src.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    comment_only = [l for l, s in zip(src.splitlines(), stripped.splitlines())
                    if l.strip() and not s.strip() and not l.lstrip().startswith("#")]
    if code and len(code) <= 12 and len(comment_only) / max(len(raw), 1) >= 0.5:
        return "unusually many explanatory comments for a trivial program (weak signal only)"
    return None


@register("similarity_flag", needs_execution=False)
class SimilarityFlag:
    def run(self, ctx):
        p = ctx.params
        thr = float(p.get("flag_threshold", 0.85))
        min_tokens = int(p.get("min_tokens", 30))
        k, w = int(p.get("k", 5)), int(p.get("window", 4))
        src = ctx.source_path.read_text(encoding="utf-8", errors="replace")
        toks = normalise_tokens(src)
        mine = fingerprints(toks, k, w)
        corpus = ctx.resolve(p.get("corpus_dir", "corpus/"))
        problem = p.get("corpus_problem") or ctx.rules.problem
        me = ctx.source_path.resolve()
        stored = [c for c in corpus_files(corpus, problem) if c[0].resolve() != me]
        peers = peer_files(ctx.peers_dir, me)
        files = stored + peers
        matches = []
        for f, name, kind in files:
            other = fingerprints(normalise_tokens(f.read_text(encoding="utf-8", errors="replace")), k, w)
            matches.append((jaccard(mine, other), name, kind))
        matches.sort(key=lambda m: (-m[0], m[1]))
        best = matches[0] if matches else (0.0, None, None)
        ev = {"tokens": len(toks), "corpus_problem": problem, "corpus_size": len(stored),
              "peers_compared": len(peers), "max_similarity": round(best[0], 3),
              "closest": best[1], "threshold": thr,
              "top_matches": [{"file": m[1], "similarity": round(m[0], 3), "kind": m[2]} for m in matches[:3]]}
        if not files:
            ev["note"] = "corpus and peers are empty or missing: nothing to compare against"
        flags = []
        hint = _style_hint(src)
        if hint:
            ev["style_hint"] = hint
            flags.append({"kind": "style_hint", "detail": hint})
        too_short = len(toks) < min_tokens
        if too_short:
            ev["note"] = f"program has {len(toks)} tokens (< {min_tokens}): too short to flag reliably"
        over = [m for m in matches if m[0] > thr]
        if over and not too_short:
            for sim, rel, kind in over[:3]:
                flags.insert(0, {"kind": kind, "detail": f"{sim:.2f} similarity with {rel} "
                                                         f"(threshold {thr:g}); needs human review"})
        flagged = bool(over) and not too_short
        score = 1.0
        if flagged and p.get("penalize", True) and thr < 1.0:
            score = max(0.0, min(1.0, (1.0 - best[0]) / (1.0 - thr)))
        fb = (f"max similarity {best[0]:.2f}" + (f" with {best[1]}" if best[1] else "") +
              (" - FLAGGED for review" if flagged else " (not flagged)"))
        return AnalyzerResult(score=score, evidence=ev, feedback=fb, flags=flags,
                              suggestions=["Make sure the code is your own work; be ready to explain it."] if flagged else [])
