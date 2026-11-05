#include <stdio.h>

#define MOD 1000000007LL

long long memo[1001];

/* Memoised recursion, but the table only has room for n <= 1000. */
long long ways(int n) {
    if (n <= 1) {
        return 1;
    }
    if (memo[n] != 0) {
        return memo[n];
    }
    memo[n] = (ways(n - 1) + ways(n - 2)) % MOD;
    return memo[n];
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    printf("%lld\n", ways(n));
    return 0;
}
