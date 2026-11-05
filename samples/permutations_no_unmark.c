#include <stdio.h>

int n, perm[8], used[9];

/* used[v] is never reset after the recursive call, so only the first permutation appears. */
void gen(int pos) {
    if (pos == n) {
        for (int i = 0; i < n; i++) {
            printf("%d ", perm[i]);
        }
        printf("\n");
        return;
    }
    for (int v = 1; v <= n; v++) {
        if (!used[v]) {
            used[v] = 1;
            perm[pos] = v;
            gen(pos + 1);
        }
    }
}

int main(void) {
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    gen(0);
    return 0;
}
