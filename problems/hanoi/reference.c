/* Trusted reference solution for hanoi: the standard recursive solution. */
#include <stdio.h>

static long long moves;

static void solve(int n, char from, char to, char via) {
    if (n == 0) {
        return;
    }
    solve(n - 1, from, via, to);
    printf("Move disk %d from %c to %c\n", n, from, to);
    moves++;
    solve(n - 1, via, to, from);
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        return 1;
    }
    solve(n, 'A', 'C', 'B');
    printf("Total moves: %lld\n", moves);
    return 0;
}
