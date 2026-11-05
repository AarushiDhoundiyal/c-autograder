#include <stdio.h>

int n, col[10], d1[20], d2[20];

/* After trying a square the marks are never cleared, so later branches see stale queens. */
int solve(int row) {
    if (row == n) {
        return 1;
    }
    int count = 0;
    for (int c = 0; c < n; c++) {
        if (col[c] || d1[row - c + n - 1] || d2[row + c]) {
            continue;
        }
        col[c] = d1[row - c + n - 1] = d2[row + c] = 1;
        count += solve(row + 1);
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
