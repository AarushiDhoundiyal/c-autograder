#include <stdio.h>

/**
 * Adds two integers using a 64-bit type so the result cannot overflow
 * when both inputs fit in a 32-bit int.
 */
long long add(int x, int y) {
    return (long long)x + (long long)y;
}

int main(void) {
    int x, y;

    if (scanf("%d %d", &x, &y) != 2) {
        fprintf(stderr, "Invalid input\n");
        return 1;
    }

    printf("%lld\n", add(x, y));
    return 0;
}
