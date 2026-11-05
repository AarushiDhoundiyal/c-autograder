#include <stdio.h>

#define MOD 1000000007LL

/**
 * Number of ways to climb n stairs with steps of 1 or 2, modulo 1e9+7.
 * Uses two variables instead of a full table.
 */
long long count_ways(int n) {
    long long two_back = 1;
    long long one_back = 1;
    for (int i = 2; i <= n; i++) {
        long long current = (one_back + two_back) % MOD;
        two_back = one_back;
        one_back = current;
    }
    return one_back;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0 || n > 1000) {
        fprintf(stderr, "n must be between 0 and 1000\n");
        return 1;
    }
    printf("%lld\n", count_ways(n));
    return 0;
}
