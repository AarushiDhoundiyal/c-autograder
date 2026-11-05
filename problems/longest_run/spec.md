# longest_run

Longest run of identical characters. Read one non-empty lowercase string `S` (no spaces) and print the
length of its longest contiguous block of equal characters, followed by a newline.

Constraints: 1 <= length(S) <= 1000; every character is `a`-`z`.

Sample input: `aaabbccccdd`  Sample output: `4`

**Specification decisions.** A one-character string has answer 1. The longest run does not have to be at
the beginning. Required time complexity: O(L); O(1) extra space is possible.
