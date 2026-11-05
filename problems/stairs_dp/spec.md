# stairs_dp

Climbing stairs with a small bound. Read `N` (0 <= N <= 1000) and print the number of sequences of 1-stair
and 2-stair moves that reach exactly stair `N`, modulo 1000000007, followed by a newline.

Sample input: `5`  Sample output: `8`

**Specification decisions.** There is one (empty) sequence for `N = 0`, so the answer is 1. Apply the
modulo during the calculation to avoid overflow. Required time complexity: O(N); O(1) extra space is
possible. This is the same task as `climb_stairs` with a smaller bound on `N`.
