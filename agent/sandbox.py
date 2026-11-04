"""Safe compile-and-run.

Local mode (default) isolates a program with POSIX resource limits and a
private process group:
  * wall-clock timeout, killed with the whole process group (survives hangs
    and fork bombs),
  * CPU-time limit (RLIMIT_CPU), address-space limit (RLIMIT_AS),
  * output cap: stdout/stderr go to files limited by RLIMIT_FSIZE (1 MiB),
  * process-count limit (RLIMIT_NPROC; not enforced for root, so run the
    grader as a normal user or inside the Docker image).
Linux/macOS only. On Windows, run the grader inside WSL or Docker.

Hardening (student code is untrusted, and the grader's own files, such as the
hidden tests and the reference solution, sit on the same disk):
  * every student run starts in a fresh EMPTY directory, never in the grader's
    working directory, so relative paths such as "problems/add/tests/001.out" fail;
  * when the grader runs as root (the Docker image does) and
    AUTOGRADER_DROP_PRIVILEGES=1 is set (or Sandbox(drop_privileges=True)), student
    code runs as the unprivileged user "nobody". With the problem folders chmod 0700
    it can then not read the tests even through an absolute path. As a bonus
    RLIMIT_NPROC (fork-bomb protection) is enforced, because it is ignored for root.
Not covered: network access (use `docker run --network none`) and anything the
unprivileged user may already read on the machine.
"""
from __future__ import annotations

import math
import os
import re
import resource
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

OK = "OK"
TIMEOUT = "TIMEOUT"
RUNTIME_ERROR = "RUNTIME_ERROR"
SIGNAL = "SIGNAL"
OUTPUT_LIMIT = "OUTPUT_LIMIT"

DEFAULT_COMPILE_FLAGS = ["-O2", "-Wall", "-Wextra", "-std=c11"]
OUTPUT_LIMIT_BYTES = 1 << 20
_DEFAULT = object()


@dataclass
class RunResult:
    outcome: str
    returncode: int
    signal: str | None
    stdout: str
    stderr: str
    elapsed_s: float            # informational only, never used in a grade
    output_truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.outcome == OK


@dataclass
class CompileResult:
    ok: bool
    returncode: int
    stderr: str
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    output_path: Path | None = None


@dataclass
class _Raw:
    returncode: int
    timed_out: bool
    stdout: bytes
    stderr: bytes
    elapsed_s: float


def _spawn(argv, stdin_bytes, wall_s, cpu_s, as_bytes, fsize, nproc, cwd, env, drop_to=None) -> _Raw:
    with tempfile.TemporaryFile() as fin, tempfile.TemporaryFile() as fout, \
            tempfile.TemporaryFile() as ferr:
        fin.write(stdin_bytes)
        fin.flush()
        fin.seek(0)

        def limits():
            if cpu_s is not None:
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 1))
            if as_bytes is not None:
                resource.setrlimit(resource.RLIMIT_AS, (as_bytes, as_bytes))
            if fsize is not None:
                resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
            if nproc is not None:
                resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            if drop_to is not None:                # last step: give up root
                uid, gid = drop_to
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)

        t0 = time.monotonic()
        p = subprocess.Popen(argv, stdin=fin, stdout=fout, stderr=ferr, cwd=cwd,
                             env=env, preexec_fn=limits, start_new_session=True,
                             close_fds=True)
        timed_out = False
        try:
            p.wait(timeout=wall_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                p.kill()
            p.wait()
        try:  # sweep up stragglers left behind in the process group
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        elapsed = time.monotonic() - t0
        cap = (fsize + 1) if fsize is not None else 8 << 20
        fout.seek(0)
        ferr.seek(0)
        return _Raw(p.returncode, timed_out, fout.read(cap), ferr.read(cap), elapsed)


def _base_env(extra=None) -> dict:
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C", "LC_ALL": "C"}
    if extra:
        env.update(extra)
    return env


class Sandbox:
    def __init__(self, time_limit_s: float = 1.0, memory_limit_mb: float = 64,
                 output_limit_bytes: int = OUTPUT_LIMIT_BYTES, nproc: int = 64,
                 drop_privileges: bool | None = None, run_as_uid: int | None = None):
        if drop_privileges is None:
            drop_privileges = os.environ.get("AUTOGRADER_DROP_PRIVILEGES") == "1"
        uid = run_as_uid if run_as_uid is not None else int(os.environ.get("AUTOGRADER_RUN_UID", "65534"))
        self.drop_requested = bool(drop_privileges)
        # Only root can change user; otherwise the request cannot be honoured.
        self.drop_to = (uid, uid) if drop_privileges and os.geteuid() == 0 else None
        self.time_limit_s = time_limit_s
        self.memory_limit_mb = memory_limit_mb
        self.output_limit_bytes = output_limit_bytes
        self.nproc = nproc

    @property
    def privilege_drop_active(self) -> bool:
        return self.drop_to is not None

    # ------------------------------------------------------------------ compile
    def compile(self, source, output, flags=None, cwd=None, timeout_s: float = 60) -> CompileResult:
        source, output = Path(source), Path(output)
        if flags is None:
            flags = DEFAULT_COMPILE_FLAGS
        elif isinstance(flags, str):
            flags = shlex.split(flags)
        cwd = Path(cwd) if cwd else source.parent
        # relative source name keeps compiler messages free of temp paths
        try:
            src_arg = str(source.relative_to(cwd))
        except ValueError:
            src_arg = str(source)
        argv = ["gcc", *flags, src_arg, "-o", str(output), "-lm"]
        try:
            raw = _spawn(argv, b"", timeout_s, int(timeout_s), None, None, None,
                         str(cwd), _base_env())
        except FileNotFoundError:
            return CompileResult(False, 127, "gcc not found", [], ["compiler 'gcc' not found"])
        stderr = raw.stderr.decode("utf-8", "replace")
        lines = stderr.splitlines()
        warnings = [l for l in lines if ": warning:" in l]
        errors = [l for l in lines if re.search(r": (fatal )?error:|undefined reference|ld returned", l)]
        if raw.timed_out:
            errors.append("compilation timed out")
        ok = raw.returncode == 0 and not raw.timed_out and output.exists()
        if ok and self.drop_to is not None:
            # the unprivileged user must be able to run the binary and write
            # tool output (e.g. callgrind files) next to it
            os.chmod(output.parent, 0o777)
            os.chmod(output, 0o755)
        return CompileResult(ok, raw.returncode, stderr, warnings, errors,
                             output if ok else None)

    # ---------------------------------------------------------------------- run
    def run(self, argv, stdin: str = "", time_limit_s=_DEFAULT, memory_limit_mb=_DEFAULT,
            cwd=None, env=None, output_limit_bytes=None, nproc=_DEFAULT,
            trusted: bool = False) -> RunResult:
        """Run a command under limits. memory_limit_mb=None disables the
        address-space limit (needed for AddressSanitizer builds); nproc=None
        disables the process-count limit (needed by tools that start threads).
        cwd=None means a fresh empty directory (removed afterwards), not the
        grader's directory. trusted=True is for the grader's own tools (cppcheck):
        they keep the grader's user and may use the real file system."""
        wall = self.time_limit_s if time_limit_s is _DEFAULT else time_limit_s
        mem = self.memory_limit_mb if memory_limit_mb is _DEFAULT else memory_limit_mb
        cap = output_limit_bytes or self.output_limit_bytes
        as_bytes = int(mem * 1024 * 1024) if mem is not None else None
        scratch = None
        if cwd is None:
            scratch = tempfile.mkdtemp(prefix="autograder_cwd_")
            os.chmod(scratch, 0o755)
            cwd = scratch
        try:
            raw = _spawn([str(a) for a in argv], stdin.encode("utf-8"), wall,
                         math.ceil(wall) + 1, as_bytes, cap,
                         self.nproc if nproc is _DEFAULT else nproc,
                         str(cwd), _base_env(env), None if trusted else self.drop_to)
        finally:
            if scratch:
                shutil.rmtree(scratch, ignore_errors=True)
        truncated = len(raw.stdout) >= cap or len(raw.stderr) >= cap
        rc, sig = raw.returncode, None
        if raw.timed_out:
            outcome = TIMEOUT
        elif rc < 0:
            sig = signal.Signals(-rc).name
            if -rc == signal.SIGXFSZ:
                outcome = OUTPUT_LIMIT
            elif -rc == signal.SIGXCPU:
                outcome = TIMEOUT
            else:
                outcome = SIGNAL
        elif rc != 0:
            outcome = RUNTIME_ERROR
        else:
            outcome = OUTPUT_LIMIT if truncated else OK
        return RunResult(outcome, rc, sig, raw.stdout[:cap].decode("utf-8", "replace"),
                         raw.stderr[:cap].decode("utf-8", "replace"), raw.elapsed_s, truncated)
