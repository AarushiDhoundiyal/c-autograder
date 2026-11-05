# nqueens

Read `n` (1 <= n <= 10) and print the number of ways to place `n` queens on an `n x n`
chessboard so that no two queens attack each other (same row, same column or same diagonal),
followed by a newline.

Sample input: `4`  Sample output: `2`

**Specification decisions.** Rotations and reflections of a solution count as different
solutions. For `n = 2` and `n = 3` the answer is `0`.
