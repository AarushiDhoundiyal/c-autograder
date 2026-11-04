import os
import pytest
from agent import sandbox as sb

ROOT_USER = hasattr(os, "geteuid") and os.geteuid() == 0


def build(tmp_path, code, flags=None):
    src = tmp_path / "p.c"; src.write_text(code)
    s = sb.Sandbox(time_limit_s=1, memory_limit_mb=64)
    res = s.compile(src, tmp_path / "p.bin", flags)
    return s, res


def test_compile_ok_and_run(tmp_path):
    s, c = build(tmp_path, '#include <stdio.h>\nint main(){int a,b;scanf("%d %d",&a,&b);printf("%d\\n",a+b);return 0;}')
    assert c.ok
    r = s.run([c.output_path], stdin="7 5\n")
    assert r.ok and r.stdout == "12\n"


def test_compile_error_reported(tmp_path):
    _, c = build(tmp_path, "int main(){ return x; }")
    assert not c.ok and c.errors and "p.c:1" in c.errors[0]


def test_warnings_counted(tmp_path):
    _, c = build(tmp_path, "int main(){int unused; return 0;}")
    assert c.ok and len(c.warnings) == 1


def test_infinite_loop_times_out_quickly(tmp_path):
    s, c = build(tmp_path, "int main(){while(1){} return 0;}")
    r = s.run([c.output_path])
    assert r.outcome == sb.TIMEOUT and r.elapsed_s < 3


def test_segfault_is_classified(tmp_path):
    s, c = build(tmp_path, "int main(){int*p=0;*p=1;return 0;}", ["-O0"])
    r = s.run([c.output_path])
    assert r.outcome == sb.SIGNAL and r.signal == "SIGSEGV"


def test_nonzero_exit(tmp_path):
    s, c = build(tmp_path, "int main(){return 3;}")
    r = s.run([c.output_path])
    assert r.outcome == sb.RUNTIME_ERROR and r.returncode == 3


def test_output_flood_is_capped(tmp_path):
    s, c = build(tmp_path, '#include <stdio.h>\nint main(){for(;;)putchar(\'x\');}')
    r = s.run([c.output_path], time_limit_s=3)
    assert r.outcome == sb.OUTPUT_LIMIT and len(r.stdout) <= sb.OUTPUT_LIMIT_BYTES


def test_memory_hog_is_stopped(tmp_path):
    code = '#include <stdlib.h>\n#include <string.h>\nint main(){char*p=malloc(400u<<20);if(!p)return 7;memset(p,1,400u<<20);return 0;}'
    s, c = build(tmp_path, code, ["-O0"])
    r = s.run([c.output_path])
    assert r.outcome != sb.OK


@pytest.mark.skipif(ROOT_USER, reason="RLIMIT_NPROC is not enforced for root; run as a normal user or in Docker")
def test_fork_bomb_is_contained(tmp_path):
    s, c = build(tmp_path, '#include <unistd.h>\nint main(){for(;;)fork();}', ["-O0"])
    r = s.run([c.output_path])
    assert r.outcome in (sb.TIMEOUT, sb.SIGNAL, sb.RUNTIME_ERROR)
