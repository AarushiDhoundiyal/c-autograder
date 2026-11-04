/* Trusted reference solution for sum_array: n, then n integers; print their sum (long long). */
#include <stdio.h>

int main(void) {
    int n;
    long long total = 0;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        int v;
        if (scanf("%d", &v) != 1) {
            break;
        }
        total += v;
    }
    printf("%lld\n", total);
    return 0;
}
