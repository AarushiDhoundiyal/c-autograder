#include <stdio.h>
#include <string.h>

#define MOD 1000000007LL
#define MAX_N 1000

static long long memo[MAX_N + 1];

/* Top-down recursion with memoisation */
static long long ways(int n) {
    if (n <= 1) {
        return 1;
    }
    if (memo[n] != -1) {
        return memo[n];
    }
    memo[n] = (ways(n - 1) + ways(n - 2)) % MOD;
    return memo[n];
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0 || n > MAX_N) {
        return 1;
    }
    memset(memo, -1, sizeof memo);
    printf("%lld\n", ways(n));
    return 0;
}
