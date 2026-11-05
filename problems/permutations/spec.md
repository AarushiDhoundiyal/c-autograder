# permutations

Read `n` (1 <= n <= 8) and print every permutation of the numbers `1 2 ... n` in
lexicographic (dictionary) order, one permutation per line, with the numbers separated by
single spaces.

Sample input: `3`  Sample output:

    1 2 3
    1 3 2
    2 1 3
    2 3 1
    3 1 2
    3 2 1

**Specification decisions.** The order matters: a program that prints every permutation in a
different order is marked wrong. There are `n!` lines (40320 for `n = 8`).
