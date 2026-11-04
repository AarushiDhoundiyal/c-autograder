/* Trusted reference solution for add_two_integers.
   The exact mathematical sum is computed in long long, so INT_MAX + 1 prints 2147483648. */
#include <stdio.h>

int main(void) {
    long long a, b;
    if (scanf("%lld %lld", &a, &b) != 2) {
        return 1;
    }
    printf("%lld\n", a + b);
    return 0;
}
