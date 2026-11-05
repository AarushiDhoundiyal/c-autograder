# lis

Longest increasing subsequence. The first integer `n` (0 <= n <= 5000) is the length of the
sequence; `n` 32-bit integers follow, separated by whitespace or newlines. Print the length of
the longest **strictly** increasing subsequence, followed by a newline. A subsequence keeps the
original order but does not have to be contiguous.

Sample input:

    8
    10 9 2 5 3 7 101 18

Sample output: `4`

**Specification decisions.** Equal values do not count as increasing (`2 2` has length 1).
`n = 0` prints `0`. Required time complexity: O(n^2) or better.
