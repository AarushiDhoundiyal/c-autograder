#include <stdio.h>

int moves = 0;

/* The first recursive call swaps the target and spare pegs, so the moves are wrong. */
void hanoi(int n, char from, char to, char via) {
    if (n == 0) {
        return;
    }
    hanoi(n - 1, from, to, via);
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
