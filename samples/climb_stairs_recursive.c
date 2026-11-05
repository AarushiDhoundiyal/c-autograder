#include <stdio.h>

#define MOD 1000000007LL

/* Correct recurrence, but plain recursion recomputes the same values: exponential time. */
static long long ways(int n) {
    if (n <= 1) {
        return 1;
    }
    return (ways(n - 1) + ways(n - 2)) % MOD;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    printf("%lld\n", ways(n));
    return 0;
}
