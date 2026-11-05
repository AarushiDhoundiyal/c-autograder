"""Tests for counter-tests, edge cases, complexity, LLM review and similarity."""
import json
import re
import shutil
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from agent import counter_tests as ct, profiling
from agent.coordinator import grade_submission
from agent.similarity import similarity, normalise_tokens
from analyzers import complexity_estimator as cx, llm_review as lr
from tests.helpers import SAMPLES, make_add_tests

ROOT = Path(__file__).resolve().parent.parent
EDGE = ROOT / "problems" / "add" / "edge_cases.json"
HAVE_VALGRIND = shutil.which("valgrind") is not None


def rules_for(tmp_path, metrics, name="rules.json"):
    p = tmp_path / name
    p.write_text(json.dumps({"problem": "add", "time_limit_s": 1, "memory_limit_mb": 64,
                             "smoke_input": "7 5\n", "metrics": metrics}))
    return p


def one_metric(tmp_path, analyzer, params, name="m"):
    return rules_for(tmp_path, [{"name": name, "analyzer": analyzer, "weight": 1.0, "params": params}])


def metric(rep, name):
    return next(m for m in rep["metrics"] if m["name"] == name)


# ----------------------------------------------------------- counter-test engine
def test_seed_and_random_inputs_are_reproducible():
    assert ct.derive_seed("h", "add") == ct.derive_seed("h", "add")
    assert ct.derive_seed("h", "add") != ct.derive_seed("h2", "add")
    spec = ct.load_edge_cases(EDGE)
    a = ct.collect_inputs(spec, ["random"], 7)
    assert a == ct.collect_inputs(spec, ["random"], 7) and a != ct.collect_inputs(spec, ["random"], 8)
    assert len(a) == 20


def test_unknown_group_is_an_error():
    with pytest.raises(ValueError):
        ct.collect_inputs(ct.load_edge_cases(EDGE), ["nonsense"], 1)


def test_minimise_shrinks_numbers_toward_zero():
    fails = lambda t: int(t.split()[0]) - int(t.split()[1]) != int(t.split()[0]) + int(t.split()[1])
    assert ct.minimise("700 500\n", fails) == "0 1\n"       # smallest input where a-b != a+b
    assert ct.minimise("7 5\n", lambda t: t.strip() == "7 5") == "7 5\n"   # cannot shrink


def test_minimise_budget_is_respected():
    calls = []
    ct.minimise("1000 2000 3000\n", lambda t: calls.append(t) or True, budget=10)
    assert len(calls) <= 10


def test_show_input_keeps_whitespace_visible():
    assert ct.show_input("7 5\n") == "7 5"
    assert ct.show_input("7 5\r\n") == repr("7 5\r\n")
    assert ct.show_input("7 5") == repr("7 5")


# ------------------------------------------------------------- edge_case_runner
@pytest.fixture
def edge_rules(tmp_path):
    return one_metric(tmp_path, "edge_case_runner",
                      {"reference": str(SAMPLES / "add_good.c"), "edge_cases_file": str(EDGE)})


def test_edge_cases_good_submission_passes_everything(edge_rules):
    m = metric(grade_submission(SAMPLES / "add_good.c", edge_rules), "m")
    assert m["status"] == "ok" and m["score"] == 1.0 and m["evidence"]["counter_tests_found"] == 0


def test_edge_cases_expose_overflow_with_minimal_input(edge_rules):
    m = metric(grade_submission(SAMPLES / "add_basic.c", edge_rules), "m")
    assert 0 < m["score"] < 1
    ev = m["evidence"]
    assert ev["groups"]["int_overflow"]["passed"] < ev["groups"]["int_overflow"]["total"]
    assert ev["groups"]["negatives"]["passed"] == ev["groups"]["negatives"]["total"]
    f = ev["failing"][0]
    assert f["kind"] == "overflow" and "32-bit" in f["why"]
    assert f["expected"] != f["got"] and f["expected"].lstrip("-").isdigit()


def test_edge_cases_crash_is_classified(edge_rules):
    m = metric(grade_submission(SAMPLES / "add_crash.c", edge_rules), "m")
    assert m["score"] == 0.0 and m["evidence"]["failing"][0]["kind"] == "crash"


def test_edge_cases_skipped_when_program_does_not_compile(edge_rules):
    rep = grade_submission(SAMPLES / "add_broken.c", edge_rules)
    assert metric(rep, "m")["status"] == "skipped" and rep["partial"]


def test_edge_cases_selected_groups_and_reproducibility(tmp_path):
    rules = one_metric(tmp_path, "edge_case_runner",
                       {"reference": str(SAMPLES / "add_good.c"), "edge_cases_file": str(EDGE),
                        "cases": ["zero", "random"], "random_count": 8})
    a = grade_submission(SAMPLES / "add_basic.c", rules)
    b = grade_submission(SAMPLES / "add_basic.c", rules)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert set(metric(a, "m")["evidence"]["groups"]) == {"zero", "random"}


def test_edge_cases_bad_reference_reports_error(tmp_path):
    rules = one_metric(tmp_path, "edge_case_runner",
                       {"reference": str(SAMPLES / "add_broken.c"), "edge_cases_file": str(EDGE)})
    m = metric(grade_submission(SAMPLES / "add_good.c", rules), "m")
    assert m["status"] == "error" and "reference" in m["feedback"]


# ---------------------------------------------------------------------- complexity
def test_parse_class_variants():
    assert [cx.parse_class(x) for x in ("O(1)", "o(log n)", "O(N)", "O(n log n)", "O(n^2)", "O(n2)")] == [0, 1, 2, 3, 4, 4]
    with pytest.raises(ValueError):
        cx.parse_class("fast")


def test_exponent_bands_and_fit():
    import math
    assert [cx.class_from_slope(k) for k in (0.0, 0.4, 1.0, 1.3, 2.0, 3.0)] == [0, 1, 2, 3, 4, 5]
    sizes = [1000, 2000, 4000, 8000]
    k, r2 = cx.fit_power(sizes, [200000 + 5 * n for n in sizes])
    assert abs(k - 1.0) < 0.02 and r2 > 0.999
    k, _ = cx.fit_power(sizes, [200000 + n * n for n in sizes])
    assert abs(k - 2.0) < 0.02
    k, _ = cx.fit_power(sizes, [200000 + int(5 * n * math.log2(n)) for n in sizes])
    assert cx.class_from_slope(k) == 3                      # n log n
    assert cx.fit_power([1, 10, 100], [5000, 5000, 5000]) == (None, None)
    assert cx.fit_power([1, 10], [5000, 6000]) == (None, None)


def test_pure_python_fit_matches_numpy():
    xs, ys = [1.0, 2.0, 3.5, 5.0], [2.1, 3.9, 7.2, 9.8]
    m1, b1 = cx._polyfit(xs, ys)
    saved, cx._np = cx._np, None
    try:
        m2, b2 = cx._polyfit(xs, ys)
    finally:
        cx._np = saved
    assert abs(m1 - m2) < 1e-9 and abs(b1 - b2) < 1e-9


@pytest.mark.parametrize("code,depth", [
    ("int main(){return 0;}", 0),
    ("int main(){int i;for(i=0;i<5;i++){}return 0;}", 1),
    ("int main(){int i,j;for(i=0;i<5;i++){for(j=0;j<5;j++){x++;}}}", 2),
    ("int main(){for(;;) for(;;) x++;}", 2),
    ("int main(){int i=0;do{i++;}while(i<9);return 0;}", 1),
    ("int main(){while(a){for(;;){for(;;){}}}}", 3),
    ("int main(){for(;;){a;} for(;;){b;}}", 1),
    ("/* for(;;){for(;;){}} */ int main(){puts(\"while(1){\");}", 0),
])
def test_static_loop_depth(code, depth):
    assert cx.static_estimate(code)["loop_depth"] == depth


def test_static_detects_recursion():
    s = cx.static_estimate("int f(int n){ if(n<2) return n; return f(n-1)+f(n-2);} int main(){return f(5);}")
    assert s["recursion"] and s["class"] >= 2


def complexity_rules(tmp_path, **params):
    return one_metric(tmp_path, "complexity_estimator", params)


def test_complexity_static_fallback_on_sample(tmp_path):
    m = metric(grade_submission(SAMPLES / "add_good.c",
                                complexity_rules(tmp_path, required="O(1)", method="static")), "m")
    assert m["score"] == 1.0 and m["evidence"]["method"] == "static_loop_depth"
    assert m["evidence"]["confidence"] == "low"


LINEAR = '#include <stdio.h>\nint main(){int n;long long s=0;scanf("%d",&n);for(int i=0;i<n;i++)s+=i;printf("%lld\\n",s);return 0;}\n'
QUAD = '#include <stdio.h>\nint main(){int n;long long s=0;scanf("%d",&n);for(int i=0;i<n;i++)for(int j=0;j<n;j++)s+=j;printf("%lld\\n",s);return 0;}\n'


@pytest.mark.skipif(not HAVE_VALGRIND, reason="valgrind not installed")
@pytest.mark.parametrize("code,estimated,required,score", [
    (LINEAR, "O(n)", "O(n)", 1.0), (LINEAR, "O(n)", "O(1)", 0.0),
    (QUAD, "O(n^2)", "O(n log n)", 0.5), (QUAD, "O(n^2)", "O(n)", 0.0), (QUAD, "O(n^2)", "O(n^2)", 1.0)])
def test_complexity_callgrind_classifies_programs(tmp_path, code, estimated, required, score):
    src = tmp_path / "prog.c"
    src.write_text(code)
    rules = complexity_rules(tmp_path, required=required, generator="single_n",
                             sizes=[1000, 2000, 4000, 8000])
    m = metric(grade_submission(src, rules), "m")
    assert m["evidence"]["method"] == "callgrind"
    assert m["evidence"]["estimated"] == estimated and m["score"] == score
    assert m["evidence"]["r_squared"] > 0.99


@pytest.mark.skipif(not HAVE_VALGRIND, reason="valgrind not installed")
def test_complexity_constant_program_and_determinism(tmp_path):
    rules = complexity_rules(tmp_path, required="O(1)", sizes=[1, 10, 100])
    a = grade_submission(SAMPLES / "add_good.c", rules)
    b = grade_submission(SAMPLES / "add_good.c", rules)
    assert metric(a, "m")["evidence"]["estimated"] == "O(1)" and metric(a, "m")["score"] == 1.0
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


@pytest.mark.skipif(not HAVE_VALGRIND, reason="valgrind not installed")
def test_complexity_small_sizes_fall_back_to_static(tmp_path):
    src = tmp_path / "prog.c"
    src.write_text(QUAD)
    m = metric(grade_submission(src, complexity_rules(tmp_path, required="O(1)", generator="single_n",
                                                      sizes=[1, 2, 3])), "m")
    assert m["evidence"]["method"] == "static_loop_depth" and m["evidence"]["estimated"] == "O(n^2)"


EXPONENTIAL = ('#include <stdio.h>\nlong long f(int n){return n<2?n:f(n-1)+f(n-2);}\n'
               'int main(){int n;scanf("%d",&n);printf("%lld\\n",f(n));return 0;}\n')
CRASH = '#include <stdio.h>\nint main(){int n;scanf("%d",&n);for(int i=0;i<n;i++){}int *p=0;*p=n;return 0;}\n'


@pytest.mark.skipif(not HAVE_VALGRIND, reason="valgrind not installed")
def test_complexity_program_that_does_not_finish_scores_zero(tmp_path):
    src = tmp_path / "prog.c"
    src.write_text(EXPONENTIAL)
    rules = complexity_rules(tmp_path, required="O(n)", generator="single_n", sizes=[10, 20, 40],
                             timeout_s=2)
    m = metric(grade_submission(src, rules), "m")
    assert m["score"] == 0.0 and m["evidence"]["estimated"] == "did not finish"
    assert "did not finish" in m["evidence"]["note"]


@pytest.mark.skipif(not HAVE_VALGRIND, reason="valgrind not installed")
def test_complexity_crashed_run_is_not_counted(tmp_path):
    src = tmp_path / "prog.c"
    src.write_text(CRASH)
    rules = complexity_rules(tmp_path, required="O(n)", generator="single_n", sizes=[1000, 2000, 4000])
    m = metric(grade_submission(src, rules), "m")
    assert m["evidence"]["method"] == "static_loop_depth" and "could not be measured" in m["evidence"]["note"]


@pytest.mark.skipif(not HAVE_VALGRIND, reason="valgrind not installed")
def test_profiling_helpers(tmp_path):
    from agent import sandbox
    sb = sandbox.Sandbox(10, 256)
    out = tmp_path / "a.bin"
    assert sb.compile(SAMPLES / "add_leak.c", out, ["-g", "-O0"]).ok
    info = profiling.profile_program(sb, out, "7 5\n", tmp_path)
    assert info["callgrind_instructions"] > 0
    assert info["memcheck"]["definitely_lost_bytes"] > 0          # add_leak leaks


# ------------------------------------------------------------------- readability
def test_deterministic_features_rank_samples():
    good = lr.deterministic_score(lr.deterministic_features((SAMPLES / "add_good.c").read_text()))
    basic = lr.deterministic_score(lr.deterministic_features((SAMPLES / "add_basic.c").read_text()))
    assert good > 0.8 > 0.5 > basic
    f = lr.deterministic_features((SAMPLES / "add_basic.c").read_text())
    assert f["short_names"] == ["a", "b"] and f["comment_ratio"] == 0


def test_declared_names_handles_lists_params_and_pointers():
    s = "int add(int lhs, int rhs){ int *p, q=3; char buf[10]; for(int i=0;i<3;i++){} return 0;}"
    assert lr.declared_names(s) == ["lhs", "rhs", "p", "q", "buf", "i"]


def test_comment_detection_ignores_strings():
    assert lr._comment_lines('char *u = "http://x"; // real\nint a; /* multi\nline */\nint b;') == {0, 1, 2}


def test_parse_llm_reply():
    assert lr.parse_llm_reply('{"score": 7, "reasons": ["clear"]}') == {"score": 7, "reasons": ["clear"]}
    assert lr.parse_llm_reply("score: high") is None
    assert lr.parse_llm_reply('x {"score": 99} y')["score"] == 10


class FakeOllama:
    def __init__(self, reply):
        outer = self
        self.requests = []

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append(body)
                data = json.dumps({"response": reply}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass
        self.srv = HTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()


def llm_rules(tmp_path, **params):
    base = {"model": "fake:1", "seed": 42, "temperature": 0, "cache_dir": str(tmp_path / "cache")}
    return one_metric(tmp_path, "llm_review", {**base, **params})


def test_llm_review_uses_fixed_options_and_cache(tmp_path):
    fake = FakeOllama('{"score": 5, "reasons": ["terse names", "no comments"]}')
    try:
        rules = llm_rules(tmp_path, host=fake.url, llm_share=0.4)
        a = metric(grade_submission(SAMPLES / "add_basic.c", rules), "m")
        b = metric(grade_submission(SAMPLES / "add_basic.c", rules), "m")
    finally:
        fake.close()
    assert len(fake.requests) == 1                      # second run came from the cache
    opts = fake.requests[0]["options"]
    assert opts["temperature"] == 0 and opts["seed"] == 42 and fake.requests[0]["format"] == "json"
    assert a["evidence"]["llm"]["cached"] is False and b["evidence"]["llm"]["cached"] is True
    det = a["evidence"]["deterministic_score"]
    assert abs(a["score"] - (0.6 * det + 0.4 * 0.5)) < 1e-3 and a["score"] == b["score"]
    assert any(s.startswith("Reviewer:") for s in a["suggestions"])


def test_llm_review_falls_back_when_ollama_is_down(tmp_path):
    rules = llm_rules(tmp_path, host="http://127.0.0.1:9", timeout_s=2)
    m = metric(grade_submission(SAMPLES / "add_basic.c", rules), "m")
    assert m["status"] == "ok" and m["evidence"]["llm"]["used"] is False
    assert m["score"] == m["evidence"]["deterministic_score"]


def test_llm_review_require_llm_makes_it_an_error(tmp_path):
    rules = llm_rules(tmp_path, host="http://127.0.0.1:9", timeout_s=2, require_llm=True)
    assert metric(grade_submission(SAMPLES / "add_basic.c", rules), "m")["status"] == "error"


def test_llm_review_bad_reply_is_not_cached(tmp_path):
    fake = FakeOllama("I think it is fine")
    try:
        m = metric(grade_submission(SAMPLES / "add_basic.c", llm_rules(tmp_path, host=fake.url)), "m")
    finally:
        fake.close()
    assert m["evidence"]["llm"]["used"] is False and not list((tmp_path / "cache").glob("*.json"))


# -------------------------------------------------------------------- similarity
def test_similarity_ignores_renaming_comments_and_spacing():
    a = (SAMPLES / "add_good.c").read_text()
    b = a.replace("add", "plus").replace("// ", "// totally different ")
    assert similarity(a, b) == 1.0
    assert similarity(a, (SAMPLES / "add_loop.c").read_text()) < 0.6
    assert "ID" in normalise_tokens("int foo = 3;") and "NUM" in normalise_tokens("int foo = 3;")


BIG = """#include <stdio.h>
int fact(int n){ int r = 1; for (int i = 2; i <= n; i++) { r *= i; } return r; }
int main(void){ int n; if (scanf("%d", &n) != 1) { return 1; } printf("%d\\n", fact(n)); return 0; }
"""


def sim_rules(tmp_path, corpus, **extra):
    return one_metric(tmp_path, "similarity_flag", {"corpus_dir": str(corpus), "flag_threshold": 0.85,
                                                     "min_tokens": 30, **extra})


def test_similarity_uses_only_the_corpus_of_its_own_problem(tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "llm" / "other_problem").mkdir(parents=True)
    (corpus / "llm" / "other_problem" / "fact.c").write_text(BIG)
    sub = tmp_path / "sub.c"
    sub.write_text(BIG)
    rep = grade_submission(sub, sim_rules(tmp_path, corpus))
    assert metric(rep, "m")["evidence"]["corpus_size"] == 0 and not rep["flags"]
    (corpus / "llm" / "add").mkdir()
    (corpus / "llm" / "add" / "fact.c").write_text(BIG)
    rep = grade_submission(sub, sim_rules(tmp_path, corpus))
    m = metric(rep, "m")
    assert m["evidence"]["closest"] == "llm/add/fact.c" and m["evidence"]["corpus_problem"] == "add"
    assert any(f["kind"] == "llm_copy" for f in rep["flags"])


def test_similarity_compares_with_classmates_but_not_itself(tmp_path):
    peers = tmp_path / "submissions"
    peers.mkdir()
    (peers / "bob.c").write_text(BIG)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    rep = grade_submission(peers / "bob.c", sim_rules(tmp_path, corpus), peers_dir=peers)
    assert metric(rep, "m")["evidence"]["peers_compared"] == 0 and not rep["flags"]
    (peers / "alice.c").write_text(BIG.replace("fact", "factorial").replace("r ", "result "))
    rep = grade_submission(peers / "bob.c", sim_rules(tmp_path, corpus), peers_dir=peers)
    m = metric(rep, "m")
    assert m["evidence"]["peers_compared"] == 1 and m["evidence"]["closest"] == "peers/alice.c"
    assert any(f["kind"] == "similarity" and "peers/alice.c" in f["detail"] for f in rep["flags"])


def test_similarity_flags_renamed_copy_from_llm_corpus(tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "llm").mkdir(parents=True)
    (corpus / "llm" / "fact.c").write_text(BIG)
    sub = tmp_path / "sub.c"
    sub.write_text(re.sub(r"\br\b", "acc", BIG.replace("fact", "calc")))
    rep = grade_submission(sub, sim_rules(tmp_path, corpus))
    m = metric(rep, "m")
    assert m["evidence"]["max_similarity"] > 0.85 and m["score"] < 1.0
    assert rep["flags"][0]["kind"] == "llm_copy" and "llm/fact.c" in rep["flags"][0]["detail"]


def test_similarity_does_not_flag_independent_or_short_programs(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "fact.c").write_text(BIG)
    sub = tmp_path / "sub.c"
    sub.write_text("#include <stdio.h>\nint main(void){long long a,b;scanf(\"%lld %lld\",&a,&b);"
                   "while(a>0){b+=a;a--;}printf(\"%lld\\n\",b);return 0;}\n")
    rep = grade_submission(sub, sim_rules(tmp_path, corpus))
    assert metric(rep, "m")["score"] == 1.0 and not rep["flags"]
    short = tmp_path / "short.c"
    short.write_text("int main(){return 0;}\n")
    (corpus / "short_copy.c").write_text("int main(){return 0;}\n")
    rep = grade_submission(short, sim_rules(tmp_path, corpus))
    assert not rep["flags"] and "too short" in metric(rep, "m")["evidence"]["note"]


def test_similarity_skips_itself_and_handles_missing_corpus(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "mine.c").write_text(BIG)
    rep = grade_submission(corpus / "mine.c", sim_rules(tmp_path, corpus))
    assert metric(rep, "m")["evidence"]["corpus_size"] == 0
    rep = grade_submission(corpus / "mine.c", sim_rules(tmp_path, tmp_path / "nope"))
    assert metric(rep, "m")["status"] == "ok" and "corpus" in metric(rep, "m")["evidence"]["note"]


# ---------------------------------------------------------- all nine metrics
def nine_metric_rules(tmp_path):
    tests = make_add_tests(tmp_path / "tests")
    corpus = tmp_path / "corpus"
    (corpus / "llm").mkdir(parents=True)
    (corpus / "llm" / "x.c").write_text(BIG)
    w = [0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    specs = [("correctness", "io_tests", {"testset_dir": str(tests)}),
             ("syntax", "compiler_warnings", {"flags": "-Wall -Wextra -std=c11"}),
             ("structure", "static_analysis", {"max_cyclomatic": 8, "max_function_length": 40}),
             ("modularity", "function_split", {"expect_helpers": True, "min_functions": 2}),
             ("logical", "edge_case_runner", {"reference": str(SAMPLES / "add_good.c"), "edge_cases_file": str(EDGE)}),
             ("complexity", "complexity_estimator", {"required": "O(1)", "sizes": [1, 10, 100]}),
             ("memory_safety", "sanitizer_run", {"testset_dir": str(tests)}),
             ("readability", "llm_review", {"backend": "none"}),
             ("originality", "similarity_flag", {"corpus_dir": str(corpus)})]
    return rules_for(tmp_path, [{"name": n, "analyzer": a, "weight": x, "params": p}
                                for (n, a, p), x in zip(specs, w)])


def test_all_nine_metrics_run_and_are_reproducible(tmp_path):
    rules = nine_metric_rules(tmp_path)
    reports = [grade_submission(SAMPLES / "add_basic.c", rules) for _ in range(3)]
    assert len({json.dumps(r, sort_keys=True) for r in reports}) == 1
    rep = reports[0]
    assert all(m["status"] == "ok" for m in rep["metrics"]), [(m["name"], m["feedback"]) for m in rep["metrics"] if m["status"] != "ok"]
    assert not rep["partial"] and 0 < rep["grade"] < 100
    assert abs(sum(m["weight"] for m in rep["metrics"]) - 1.0) < 1e-9
    good = grade_submission(SAMPLES / "add_good.c", rules)
    assert good["grade"] > rep["grade"]
