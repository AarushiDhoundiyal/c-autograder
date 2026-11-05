#include <stdio.h>

#define MOD 1000000007LL

/* Bottom-up DP: only the last two values are needed. */
static long long count_ways(int steps) {
    long long before_last = 1, last = 1;
    for (int i = 2; i <= steps; i++) {
        long long current = (before_last + last) % MOD;
        before_last = last;
        last = current;
    }
    return last;
}

int main(void) {
    int steps;
    if (scanf("%d", &steps) != 1 || steps < 0) {
        return 1;
    }
    printf("%lld\n", count_ways(steps));
    return 0;
}
