#include <stdio.h>

#define MOD 1000000007

int main() {
    int n;
    scanf("%d", &n);

    long long dp[1001];
    dp[0] = 1;
    dp[1] = 1;

    // dp[i] = dp[i-1] + dp[i-2]
    for (int i = 2; i <= n; i++) {
        dp[i] = (dp[i - 1] + dp[i - 2]) % MOD;
    }

    printf("%lld\n", dp[n]);
    return 0;
}
