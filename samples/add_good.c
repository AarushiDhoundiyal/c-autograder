#include <stdio.h>

/* Return the exact sum of two integers (widened so INT_MAX + 1 cannot overflow). */
static long long add(long long lhs, long long rhs) {
    return lhs + rhs;
}

int main(void) {
    int lhs, rhs;
    if (scanf("%d %d", &lhs, &rhs) != 2) {
        return 1;
    }
    printf("%lld\n", add(lhs, rhs));
    return 0;
}
