/* Trusted reference solution for knapsack: one-dimensional 0/1 DP over the capacity. */
#include <stdio.h>

#define MAX_W 10000

static long long best[MAX_W + 1];

int main(void) {
    int n, cap;
    if (scanf("%d %d", &n, &cap) != 2 || n < 0 || cap < 0 || cap > MAX_W) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        int w;
        long long v;
        if (scanf("%d %lld", &w, &v) != 2) {
            return 1;
        }
        for (int c = cap; c >= w; c--) {
            if (best[c - w] + v > best[c]) {
                best[c] = best[c - w] + v;
            }
        }
    }
    printf("%lld\n", best[cap]);
    return 0;
}
