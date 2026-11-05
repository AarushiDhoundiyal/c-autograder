#include <stdio.h>

long long best[10001];

/* Capacities go upwards, so an item can be added again and again (unbounded knapsack). */
void add_item(int cap, int w, long long v) {
    for (int c = w; c <= cap; c++) {
        if (best[c - w] + v > best[c]) {
            best[c] = best[c - w] + v;
        }
    }
}

int main(void) {
    int n, cap;
    if (scanf("%d %d", &n, &cap) != 2) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        int w;
        long long v;
        if (scanf("%d %lld", &w, &v) != 2) {
            return 1;
        }
        add_item(cap, w, v);
    }
    printf("%lld\n", best[cap]);
    return 0;
}
