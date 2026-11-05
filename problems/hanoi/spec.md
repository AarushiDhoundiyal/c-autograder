# hanoi

Tower of Hanoi. Read `n` (0 <= n <= 12), the number of disks stacked on peg `A`, smallest
(disk 1) on top. Move all disks to peg `C`, using peg `B` as spare, with the standard
recursive method: move the top `n-1` disks from `A` to `B`, move disk `n` from `A` to `C`,
then move the `n-1` disks from `B` to `C`.

Print one line per move in the form `Move disk <k> from <X> to <Y>`, and finish with the line
`Total moves: <m>`.

Sample input: `2`  Sample output:

    Move disk 1 from A to B
    Move disk 2 from A to C
    Move disk 1 from B to C
    Total moves: 3

**Specification decisions.** `n = 0` prints only `Total moves: 0`. The order of moves is the
one produced by the method above, which is the unique shortest solution.
