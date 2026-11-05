# knapsack

0/1 knapsack. The first line holds `n` and `W` (0 <= n <= 100, 0 <= W <= 10000): the number
of items and the capacity of the bag. Each of the next `n` lines holds the weight `w`
(1 <= w <= 10000) and the value `v` (0 <= v <= 1000000) of one item. Every item can be taken
at most once. Print the largest total value whose total weight is at most `W`, followed by a
newline.

Sample input:

    3 50
    10 60
    20 100
    30 120

Sample output: `220`

**Specification decisions.** An empty bag is allowed, so the answer is 0 when nothing fits.
Taking items greedily by value per unit weight is not correct (the sample shows this:
greedy gives 160).
