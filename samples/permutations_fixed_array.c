#include <stdio.h>

int n, perm[6], used[7];

/* Arrays sized for n <= 6; n = 7 and n = 8 write past their ends. */
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
            used[v] = 0;
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
