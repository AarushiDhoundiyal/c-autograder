/* Trusted reference solution for permutations: backtracking with a used[] array. */
#include <stdio.h>

static int n, perm[16], used[16];

static void build(int pos) {
    if (pos == n) {
        for (int i = 0; i < n; i++) {
            printf(i ? " %d" : "%d", perm[i]);
        }
        putchar('\n');
        return;
    }
    for (int v = 1; v <= n; v++) {
        if (!used[v]) {
            used[v] = 1;
            perm[pos] = v;
            build(pos + 1);
            used[v] = 0;
        }
    }
}

int main(void) {
    if (scanf("%d", &n) != 1 || n < 1 || n > 15) {
        return 1;
    }
    build(0);
    return 0;
}
