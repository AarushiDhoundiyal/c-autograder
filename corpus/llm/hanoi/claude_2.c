#include <stdio.h>

/**
 * Recursively solves the Tower of Hanoi.
 * Moves `disks` disks from `source` to `target` using `helper`,
 * printing each move, and returns the number of moves made.
 */
long long tower_of_hanoi(int disks, char source, char target, char helper) {
    if (disks <= 0) {
        return 0;
    }
    long long count = tower_of_hanoi(disks - 1, source, helper, target);
    printf("Move disk %d from %c to %c\n", disks, source, target);
    count++;
    count += tower_of_hanoi(disks - 1, helper, target, source);
    return count;
}

int main(void) {
    int disks;
    if (scanf("%d", &disks) != 1 || disks < 0) {
        fprintf(stderr, "Invalid input\n");
        return 1;
    }
    long long total = tower_of_hanoi(disks, 'A', 'C', 'B');
    printf("Total moves: %lld\n", total);
    return 0;
}
