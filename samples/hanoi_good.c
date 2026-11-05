#include <stdio.h>

static long long move_count = 0;

/* Move `disks` disks from peg `from` to peg `to`, using peg `spare`. */
static void move_tower(int disks, char from, char to, char spare) {
    if (disks == 0) {
        return;
    }
    move_tower(disks - 1, from, spare, to);
    printf("Move disk %d from %c to %c\n", disks, from, to);
    move_count++;
    move_tower(disks - 1, spare, to, from);
}

int main(void) {
    int disks;
    if (scanf("%d", &disks) != 1 || disks < 0) {
        return 1;
    }
    move_tower(disks, 'A', 'C', 'B');
    printf("Total moves: %lld\n", move_count);
    return 0;
}
