#include <stdio.h>

static int size;
static int solutions;

/* Bitmask backtracking: each set bit marks an attacked column */
static void place(int row, unsigned cols, unsigned left, unsigned right) {
    if (row == size) {
        solutions++;
        return;
    }
    unsigned full = (1u << size) - 1;
    unsigned available = full & ~(cols | left | right);
    while (available) {
        unsigned bit = available & -available;
        available -= bit;
        place(row + 1, cols | bit, ((left | bit) << 1) & full, (right | bit) >> 1);
    }
}

int main(void) {
    if (scanf("%d", &size) != 1) {
        return 1;
    }
    place(0, 0, 0, 0);
    printf("%d\n", solutions);
    return 0;
}
