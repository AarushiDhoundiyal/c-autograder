#include <stdio.h>

/* Correct but slow: for every element it scans the whole array again to find
 * that element (an O(n^2) shape), instead of just adding it up once. */
int main(void) {
    int n, a[100000];
    long long s = 0;
    if (scanf("%d", &n) != 1) return 1;
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &a[i]) != 1) return 1;
    }
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i == j) s += a[j];
        }
    }
    printf("%lld\n", s);
    return 0;
}
