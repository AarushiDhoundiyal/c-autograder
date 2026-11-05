#include <stdio.h>
#include <stdbool.h>

#define MAX_N 10

static int size;
static bool column_taken[MAX_N];
static bool diagonal_taken[2 * MAX_N];
static bool anti_diagonal_taken[2 * MAX_N];

/* Place one queen in `row` and every following row; return the number of complete boards. */
static long long count_placements(int row) {
    if (row == size) {
        return 1;
    }
    long long total = 0;
    for (int col = 0; col < size; col++) {
        int diag = row - col + size - 1;
        int anti = row + col;
        if (column_taken[col] || diagonal_taken[diag] || anti_diagonal_taken[anti]) {
            continue;
        }
        column_taken[col] = diagonal_taken[diag] = anti_diagonal_taken[anti] = true;
        total += count_placements(row + 1);
        column_taken[col] = diagonal_taken[diag] = anti_diagonal_taken[anti] = false;
    }
    return total;
}

int main(void) {
    if (scanf("%d", &size) != 1 || size < 1 || size > MAX_N) {
        return 1;
    }
    printf("%lld\n", count_placements(0));
    return 0;
}
