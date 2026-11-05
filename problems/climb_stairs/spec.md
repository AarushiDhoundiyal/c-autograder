# climb_stairs

A staircase has `n` steps. In one move you climb either 1 step or 2 steps. Read `n`
(0 <= n <= 1000000) and print the number of different ways to reach the top, modulo
1000000007, followed by a newline.

Sample input: `4`  Sample output: `5`

**Specification decisions.** There is exactly one way to climb 0 steps (do nothing), so
`n = 0` prints `1`. The exact count grows like the Fibonacci numbers and does not fit in
64 bits for large `n`, so the answer is always reduced modulo 1000000007.
Required time complexity: O(n).
