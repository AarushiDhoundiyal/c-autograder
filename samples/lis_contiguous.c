#include <stdio.h>

/* Finds the longest increasing run of neighbours, not the longest subsequence. */
int main(void) {
    int n, prev = 0, x, run = 0, best = 0;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &x) != 1) {
            return 1;
        }
        if (i > 0 && x > prev) {
            run++;
        } else {
            run = 1;
        }
        if (run > best) {
            best = run;
        }
        prev = x;
    }
    printf("%d\n", best);
    return 0;
}
