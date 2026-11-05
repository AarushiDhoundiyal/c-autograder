/* Trusted reference solution for nqueens: row-by-row backtracking. */
#include <stdio.h>

static int n;
static int col_used[16], diag_used[32], anti_used[32];

static long long place(int row) {
    if (row == n) {
        return 1;
    }
    long long count = 0;
    for (int c = 0; c < n; c++) {
        if (col_used[c] || diag_used[row - c + n] || anti_used[row + c]) {
            continue;
        }
        col_used[c] = diag_used[row - c + n] = anti_used[row + c] = 1;
        count += place(row + 1);
        col_used[c] = diag_used[row - c + n] = anti_used[row + c] = 0;
    }
    return count;
}

int main(void) {
    if (scanf("%d", &n) != 1 || n < 1 || n > 15) {
        return 1;
    }
    printf("%lld\n", place(0));
    return 0;
}
