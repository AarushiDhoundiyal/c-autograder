#include <stdio.h>

int main(void) {
    int a, b;
    if (scanf("%d %d", &a, &b) != 2) {
        return 1;
    }
    volatile int n = 1;
    while (n > 0) {
        /* waits forever */
    }
    printf("%d\n", a + b);
    return 0;
}
