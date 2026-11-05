#include <stdio.h>

int weight[100], value[100], taken[100];

/* Greedy by value per unit weight: fast, but not optimal for 0/1 knapsack. */
int pick_best_ratio(int n, int room) {
    int best = -1;
    for (int i = 0; i < n; i++) {
        if (taken[i] || weight[i] > room) {
            continue;
        }
        if (best < 0 || (long long)value[i] * weight[best] > (long long)value[best] * weight[i]) {
            best = i;
        }
    }
    return best;
}

int main(void) {
    int n, cap;
    if (scanf("%d %d", &n, &cap) != 2) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%d %d", &weight[i], &value[i]) != 2) {
            return 1;
        }
    }
    long long total = 0;
    int room = cap;
    int i;
    while ((i = pick_best_ratio(n, room)) >= 0) {
        taken[i] = 1;
        room -= weight[i];
        total += value[i];
    }
    printf("%lld\n", total);
    return 0;
}
