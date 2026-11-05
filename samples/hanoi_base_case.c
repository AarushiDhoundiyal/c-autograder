#include <stdio.h>

int moves = 0;

/* Base case is n == 1 only, so n == 0 recurses forever and overflows the stack. */
void hanoi(int n, char from, char to, char via) {
    if (n == 1) {
        printf("Move disk 1 from %c to %c\n", from, to);
        moves++;
        return;
    }
    hanoi(n - 1, from, via, to);
    printf("Move disk %d from %c to %c\n", n, from, to);
    moves++;
    hanoi(n - 1, via, to, from);
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    hanoi(n, 'A', 'C', 'B');
    printf("Total moves: %d\n", moves);
    return 0;
}
