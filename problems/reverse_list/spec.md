# reverse_list

Read `n` (0 <= n <= 100000) followed by `n` 32-bit integers. Build a singly linked list that
holds the values in input order, reverse the list **in place** by changing the `next` links,
and print the values of the reversed list on one line, separated by single spaces, followed
by a newline. Free every node before the program ends.

Sample input:

    5
    1 2 3 4 5

Sample output: `5 4 3 2 1`

**Specification decisions.** `n = 0` prints an empty line. The program must not leak memory;
the memory-safety metric runs it under LeakSanitizer. Required time complexity: O(n).
