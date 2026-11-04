"""Light-weight C source inspection shared by the coordinator and analyzers.

Comments and string/char literals are blanked out first (length and newlines
preserved), so a "scanf" inside a comment or string can never fool a check.
Function boundaries come from tree-sitter-c when installed (and the file is
ASCII); otherwise from a brace-depth scanner. Both give the same CInfo.
Set AUTOGRADER_NO_TREE_SITTER=1 to force the scanner.
"""
from __future__ import annotations

import bisect
import os
import re
from dataclasses import dataclass, field

KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "else", "do", "case",
            "defined", "typeof", "_Alignof", "_Generic", "_Static_assert", "__attribute__"}
READERS = {"scanf", "fscanf", "getchar", "getc", "fgetc", "fgets", "gets", "getline", "fread", "read"}
WRITERS = {"printf", "fprintf", "puts", "putchar", "putc", "fputc", "fputs", "fwrite", "write"}

_HEADER = re.compile(r"(\w+)\s*\((?:[^()]|\([^()]*\))*\)\s*$", re.S)
_CALL = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_INCLUDE = re.compile(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", re.M)


@dataclass
class FuncInfo:
    name: str
    start_line: int
    end_line: int
    body: str                       # blanked body text (no comments/strings)
    calls: list = field(default_factory=list)

    @property
    def length(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass
class CInfo:
    backend: str
    functions: list
    includes: list
    calls: set
    has_main: bool
    has_reader: bool
    has_writer: bool
    main_returns: bool

    @property
    def sanity_ok(self) -> bool:
        return self.has_main and self.has_reader and self.has_writer and self.main_returns

    def sanity_notes(self) -> list:
        notes = []
        if not self.has_main:
            notes.append("no main() function found")
        if not self.has_reader:
            notes.append("no input call (scanf/fgets/getchar/...) found")
        if not self.has_writer:
            notes.append("no output call (printf/puts/putchar/...) found")
        if self.has_main and not self.main_returns:
            notes.append("main() has no return statement")
        return notes


def blank_comments_and_strings(src: str) -> str:
    """Replace comments, string/char literal contents and preprocessor lines
    with spaces, keeping every newline so line numbers stay valid."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        two = src[i:i + 2]
        if two == "//":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif two == "/*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join("\n" if ch == "\n" else " " for ch in src[i:j])); i = j
        elif c in "\"'":
            q, j = c, i + 1
            while j < n and src[j] != q and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            j = min(j, n)
            end = j + 1 if j < n and src[j] == q else j
            out.append(q + " " * max(end - i - 2, 0) + (q if end - i >= 2 else ""))
            i = end
        else:
            out.append(c); i += 1
    text = "".join(out)
    lines, res, cont = text.split("\n"), [], False
    for line in lines:
        if cont or line.lstrip().startswith("#"):
            cont = line.rstrip().endswith("\\")
            res.append(" " * len(line))
        else:
            res.append(line)
    return "\n".join(res)


def _line_index(s: str):
    return [m.start() for m in re.finditer("\n", s)]


def _scan_functions(stripped: str):
    nl = _line_index(stripped)
    line_of = lambda pos: bisect.bisect_right(nl, pos - 1) + 1 if pos > 0 else 1
    funcs, depth, header_start, cur = [], 0, 0, None
    for i, c in enumerate(stripped):
        if c == "{":
            if depth == 0:
                header = stripped[header_start:i]
                m = _HEADER.search(header)
                if m and m.group(1) not in KEYWORDS and "=" not in header:
                    cur = (m.group(1), line_of(header_start + m.start(1)), i)
                else:
                    cur = None
            depth += 1
        elif c == "}":
            depth = max(depth - 1, 0)
            if depth == 0:
                if cur:
                    funcs.append((cur[0], cur[1], line_of(i), stripped[cur[2] + 1:i]))
                    cur = None
                header_start = i + 1
        elif c == ";" and depth == 0:
            header_start = i + 1
    return funcs


_TS_PARSER = None


def _ts_parser():
    global _TS_PARSER
    if _TS_PARSER is None:
        import tree_sitter_c as tsc
        from tree_sitter import Language, Parser
        lang = Language(tsc.language())
        try:
            _TS_PARSER = Parser(lang)
        except TypeError:
            _TS_PARSER = Parser()
            _TS_PARSER.language = lang
    return _TS_PARSER


def _ts_functions(src: str, stripped: str):
    tree = _ts_parser().parse(src.encode("utf-8"))
    found = []

    def walk(node):
        if node.type == "function_definition":
            decl = node.child_by_field_name("declarator")
            while decl is not None and decl.type != "function_declarator":
                decl = decl.child_by_field_name("declarator")
            ident = decl.child_by_field_name("declarator") if decl is not None else None
            body = node.child_by_field_name("body")
            if ident is not None and body is not None and ident.type == "identifier":
                found.append((src[ident.start_byte:ident.end_byte], ident.start_point[0] + 1,
                              node.end_point[0] + 1,
                              stripped[body.start_byte + 1:body.end_byte - 1]))
            return
        for ch in node.children:
            walk(ch)

    walk(tree.root_node)
    return found


def analyze(src: str, use_tree_sitter: bool | None = None) -> CInfo:
    stripped = blank_comments_and_strings(src)
    raw_funcs, backend = None, "scanner"
    want_ts = (use_tree_sitter if use_tree_sitter is not None
               else not os.environ.get("AUTOGRADER_NO_TREE_SITTER"))
    if want_ts and src.isascii():
        try:
            raw_funcs, backend = _ts_functions(src, stripped), "tree-sitter"
        except Exception:
            raw_funcs = None
    if raw_funcs is None:
        raw_funcs, backend = _scan_functions(stripped), "scanner"

    funcs = []
    for name, s, e, body in raw_funcs:
        calls = sorted({c for c in _CALL.findall(body) if c not in KEYWORDS})
        funcs.append(FuncInfo(name, s, e, body, calls))
    all_calls = {c for f in funcs for c in f.calls}
    main = next((f for f in funcs if f.name == "main"), None)
    return CInfo(backend=backend, functions=funcs,
                 includes=_INCLUDE.findall(src), calls=all_calls,
                 has_main=main is not None,
                 has_reader=bool(all_calls & READERS),
                 has_writer=bool(all_calls & WRITERS),
                 main_returns=bool(main and re.search(r"\breturn\b", main.body)))
