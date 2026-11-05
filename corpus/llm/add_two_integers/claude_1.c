#include <stdio.h>

int main() {
    long long a, b;

    // Read two integers from input
    scanf("%lld %lld", &a, &b);

    // Print their sum (long long avoids overflow)
    printf("%lld\n", a + b);

    return 0;
}
