#include <stdio.h>

int n, col[10], diag[20];

/* Checks columns and one diagonal direction only, so some attacking boards are counted. */
int solve(int row) {
    if (row == n) {
        return 1;
    }
    int count = 0;
    for (int c = 0; c < n; c++) {
        if (col[c] || diag[row - c + n - 1]) {
            continue;
        }
        col[c] = diag[row - c + n - 1] = 1;
        count += solve(row + 1);
        col[c] = diag[row - c + n - 1] = 0;
    }
    return count;
}

int main(void) {
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    printf("%d\n", solve(0));
    return 0;
}
