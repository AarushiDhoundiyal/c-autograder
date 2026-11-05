#include <stdio.h>

int moves = 0;

// Move n disks from 'from' to 'to' using 'aux'
void hanoi(int n, char from, char to, char aux) {
    if (n == 0) {
        return;
    }
    hanoi(n - 1, from, aux, to);
    printf("Move disk %d from %c to %c\n", n, from, to);
    moves++;
    hanoi(n - 1, aux, to, from);
}

int main() {
    int n;
    scanf("%d", &n);
    hanoi(n, 'A', 'C', 'B');
    printf("Total moves: %d\n", moves);
    return 0;
}
