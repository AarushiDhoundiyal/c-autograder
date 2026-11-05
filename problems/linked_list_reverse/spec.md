# linked_list_reverse

Build a dynamically allocated singly linked list from `N` integers in input order and print its values in
reverse order. The first line holds `N`; if `N > 0`, the second line holds exactly `N` integers.

Constraints: 0 <= N <= 100; -10000 <= value <= 10000.

Sample input:

    5
    1 2 3 4 5

Sample output: `5 4 3 2 1`

**Specification decisions.** If `N = 0`, print `EMPTY`. Use real linked-list nodes, not only an array, and
free every node before exiting. Required time complexity: O(N).
