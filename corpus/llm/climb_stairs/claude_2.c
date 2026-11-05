#include <stdio.h>
#include <stdlib.h>

#define MOD 1000000007LL

/**
 * Returns the number of ways to climb n stairs taking 1 or 2 steps,
 * modulo 1e9+7, using a bottom-up dynamic programming table.
 */
long long climb_stairs(int n) {
    if (n <= 1) {
        return 1;
    }
    long long *dp = malloc((size_t)(n + 1) * sizeof(long long));
    if (dp == NULL) {
        return -1;
    }
    dp[0] = 1;
    dp[1] = 1;
    for (int i = 2; i <= n; i++) {
        dp[i] = (dp[i - 1] + dp[i - 2]) % MOD;
    }
    long long result = dp[n];
    free(dp);
    return result;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "Invalid input\n");
        return 1;
    }
    printf("%lld\n", climb_stairs(n));
    return 0;
}
