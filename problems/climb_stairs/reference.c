/* Trusted reference solution for climb_stairs: ways(n) = ways(n-1) + ways(n-2) mod 1e9+7. */
#include <stdio.h>

#define MOD 1000000007LL

int main(void) {
    long long n;
    if (scanf("%lld", &n) != 1 || n < 0) {
        return 1;
    }
    long long prev = 1, cur = 1;
    for (long long i = 2; i <= n; i++) {
        long long next = (prev + cur) % MOD;
        prev = cur;
        cur = next;
    }
    printf("%lld\n", cur);
    return 0;
}
