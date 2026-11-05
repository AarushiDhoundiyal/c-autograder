#include <stdio.h>

int best[1001];

/* The table assumes W <= 1000; larger capacities write past the end of the array. */
void add_item(int cap, int w, int v) {
    for (int c = cap; c >= w; c--) {
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
        int w, v;
        if (scanf("%d %d", &w, &v) != 2) {
            return 1;
        }
        add_item(cap, w, v);
    }
    printf("%d\n", best[cap]);
    return 0;
}
