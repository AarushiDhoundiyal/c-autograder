# count_occurrences

Count occurrences of a target in an array. The first line holds `N` and `K`; the second line holds
`N` whitespace-separated integers. Print how many of them are equal to `K`, followed by a newline.

Constraints: 1 <= N <= 1000; -10000 <= K, A[i] <= 10000.

Sample input:

    6 2
    2 3 2 -1 2 0

Sample output: `3`

**Specification decisions.** The target may be negative or zero, and duplicates are allowed.
Required time complexity: O(N); O(1) extra space is possible.
