"""Source integrity scan: does the program go looking for files or processes?

Problems in this agent are stdin -> stdout programs. A submission that opens
files, starts processes, opens sockets, or names paths such as "tests/001.out"
is either doing something the assignment does not ask for or trying to read the
hidden tests. The scan only RAISES A FLAG for the instructor; it never changes
a grade, because legitimate programs can use fopen too.

Comments are ignored (a comment that mentions fopen is harmless); string
literals are kept, because that is where file names live.
"""
from __future__ import annotations

import re

from agent import csource

CALL_GROUPS = {
    "file access": {"fopen", "freopen", "open", "openat", "opendir", "readdir", "ftw", "nftw",
                    "stat", "lstat", "access", "realpath", "getcwd", "chdir", "fchdir", "chroot"},
    "process control": {"system", "popen", "execl", "execlp", "execle", "execv", "execvp",
                        "execve", "fork", "vfork", "posix_spawn", "ptrace", "kill"},
    "network": {"socket", "connect", "bind", "listen", "accept", "gethostbyname", "getaddrinfo"},
    "dynamic loading": {"dlopen", "dlsym"},
}
_CALL_TO_GROUP = {fn: g for g, fns in CALL_GROUPS.items() for fn in fns}
_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
_SUSPICIOUS_PATH = re.compile(
    r"\.(?:out|in|ans|expected)$|(?:^|/)(?:tests?|problems?|reference|expected|corpus|hidden|rules)(?:/|\b)"
    r"|^/(?:etc|proc|home|root|tmp|var|app|work)\b|\.\./|\.c$", re.I)
_LOCAL_INCLUDE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.M)


def strip_comments_keep_strings(src: str) -> str:
    out, i, n = [], 0, len(src)
    while i < n:
        two = src[i:i + 2]
        if two == "//":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif two == "/*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join("\n" if c == "\n" else " " for c in src[i:j])); i = j
        elif src[i] in "\"'":
            q, j = src[i], i + 1
            while j < n and src[j] != q and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(src[i:j]); i = j
        else:
            out.append(src[i]); i += 1
    return "".join(out)


def scan(src: str) -> list:
    """Return findings: [{category, what, line}], in source order."""
    text = strip_comments_keep_strings(src)
    own = {f.name for f in csource.analyze(src).functions}    # student's own helpers are fine
    findings = []
    for ln, line in enumerate(text.splitlines(), 1):
        code = _STRING.sub('""', line)             # calls are judged outside string literals
        for m in _CALL.finditer(code):
            group = _CALL_TO_GROUP.get(m.group(1))
            if group and m.group(1) not in own:
                findings.append({"category": group, "what": m.group(1) + "()", "line": ln})
        is_include = bool(_LOCAL_INCLUDE.match(line)) or line.lstrip().startswith("#")
        for m in ([] if is_include else _STRING.finditer(line)):
            if _SUSPICIOUS_PATH.search(m.group(1)):
                shown = m.group(1) if len(m.group(1)) <= 40 else m.group(1)[:37] + "..."
                findings.append({"category": "path in string", "what": f'"{shown}"', "line": ln})
        inc = _LOCAL_INCLUDE.match(line)
        if inc and ("/" in inc.group(1) or ".." in inc.group(1)):
            findings.append({"category": "include of an outside file", "what": f'#include "{inc.group(1)}"', "line": ln})
    return findings


def flag_from(findings: list):
    """One review flag summarising the findings, or None."""
    if not findings:
        return None
    parts, seen = [], set()
    for f in findings:
        key = (f["category"], f["what"])
        if key not in seen:
            seen.add(key)
            parts.append(f"{f['what']} at line {f['line']} ({f['category']})")
    more = f" and {len(parts) - 4} more" if len(parts) > 4 else ""
    return {"kind": "suspicious_code",
            "detail": "; ".join(parts[:4]) + more + ". This problem only needs stdin and stdout; "
                      "check whether the program reads files it should not."}
