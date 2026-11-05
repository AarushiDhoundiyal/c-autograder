#include <stdio.h>
#include <stdbool.h>

#define MAX_N 10

static bool cols[MAX_N];
static bool main_diag[2 * MAX_N - 1];
static bool anti_diag[2 * MAX_N - 1];

/**
 * Counts the ways to place queens in rows `row`..n-1 without conflicts,
 * using boolean arrays to check columns and diagonals in O(1).
 */
static int count_solutions(int row, int n) {
    if (row == n) {
        return 1;
    }
    int total = 0;
    for (int col = 0; col < n; col++) {
        int d1 = row - col + n - 1;
        int d2 = row + col;
        if (cols[col] || main_diag[d1] || anti_diag[d2]) {
            continue;
        }
        cols[col] = main_diag[d1] = anti_diag[d2] = true;
        total += count_solutions(row + 1, n);
        cols[col] = main_diag[d1] = anti_diag[d2] = false;
    }
    return total;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 1 || n > MAX_N) {
        fprintf(stderr, "n must be between 1 and %d\n", MAX_N);
        return 1;
    }
    printf("%d\n", count_solutions(0, n));
    return 0;
}
