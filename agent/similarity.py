"""Rename-resistant code similarity: token normalisation + k-gram winnowing
(MOSS style) + Jaccard similarity of the fingerprint sets. Pure Python and
deterministic (blake2b, never Python's randomised hash())."""
from __future__ import annotations

import hashlib
import re

from agent.csource import blank_comments_and_strings

C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else",
    "enum", "extern", "float", "for", "goto", "if", "inline", "int", "long", "register",
    "restrict", "return", "short", "signed", "sizeof", "static", "struct", "switch",
    "typedef", "union", "unsigned", "void", "volatile", "while", "main"}
LIB_NAMES = {"printf", "scanf", "puts", "putchar", "getchar", "fgets", "fscanf", "fprintf",
             "sscanf", "malloc", "calloc", "realloc", "free", "strlen", "strcpy", "strcmp",
             "memcpy", "memset", "abs", "atoi", "NULL", "stdin", "stdout", "stderr", "exit"}
KEEP = C_KEYWORDS | LIB_NAMES
_TOKEN = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'|[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||'
                    r'\+\+|--|->|<<|>>|[+\-*/%&|^]=|\S')


def normalise_tokens(src: str) -> list:
    """Identifiers -> ID, numbers -> NUM, literals -> STR; comments and
    preprocessor lines are dropped. Renaming variables does not change the result."""
    out = []
    for t in _TOKEN.findall(blank_comments_and_strings(src)):
        if t[0] in "\"'":
            out.append("STR")
        elif t[0].isdigit():
            out.append("NUM")
        elif t[0].isalpha() or t[0] == "_":
            out.append(t if t in KEEP else "ID")
        else:
            out.append(t)
    return out


def _h(gram) -> int:
    return int.from_bytes(hashlib.blake2b(" ".join(gram).encode(), digest_size=8).digest(), "big")


def fingerprints(tokens: list, k: int = 5, w: int = 4) -> set:
    if not tokens:
        return set()
    if len(tokens) < k:
        return {_h(tokens)}
    hashes = [_h(tokens[i:i + k]) for i in range(len(tokens) - k + 1)]
    if len(hashes) <= w:
        return {min(hashes)}
    chosen = set()
    for i in range(len(hashes) - w + 1):
        window = hashes[i:i + w]
        chosen.add(min(window))
    return chosen


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def similarity(src_a: str, src_b: str, k: int = 5, w: int = 4) -> float:
    return jaccard(fingerprints(normalise_tokens(src_a), k, w),
                   fingerprints(normalise_tokens(src_b), k, w))
