#include <stdio.h>
#include <stdlib.h>

/**
 * Solves the 0/1 knapsack problem with a 2-D DP table.
 * table[i][c] = best value using the first i items with capacity c.
 */
long long knapsack(int n, int capacity, const int *weights, const int *values) {
    long long **table = malloc((size_t)(n + 1) * sizeof(long long *));
    for (int i = 0; i <= n; i++) {
        table[i] = calloc((size_t)capacity + 1, sizeof(long long));
    }
    for (int i = 1; i <= n; i++) {
        for (int c = 0; c <= capacity; c++) {
            table[i][c] = table[i - 1][c];
            if (weights[i - 1] <= c) {
                long long take = table[i - 1][c - weights[i - 1]] + values[i - 1];
                if (take > table[i][c]) {
                    table[i][c] = take;
                }
            }
        }
    }
    long long best = table[n][capacity];
    for (int i = 0; i <= n; i++) {
        free(table[i]);
    }
    free(table);
    return best;
}

int main(void) {
    int n, capacity;
    if (scanf("%d %d", &n, &capacity) != 2) {
        return 1;
    }
    int *weights = malloc((size_t)(n > 0 ? n : 1) * sizeof(int));
    int *values = malloc((size_t)(n > 0 ? n : 1) * sizeof(int));
    for (int i = 0; i < n; i++) {
        scanf("%d %d", &weights[i], &values[i]);
    }
    printf("%lld\n", knapsack(n, capacity, weights, values));
    free(weights);
    free(values);
    return 0;
}
