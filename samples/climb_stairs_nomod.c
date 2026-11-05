#include <stdio.h>

/* Forgets the modulo: wrong once the count passes 1000000007, overflows after n = 91. */
static long long count_ways(int n) {
    long long a = 1, b = 1;
    for (int i = 2; i <= n; i++) {
        long long c = a + b;
        a = b;
        b = c;
    }
    return b;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    printf("%lld\n", count_ways(n));
    return 0;
}
