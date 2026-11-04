#include <stdio.h>

int main(void) {
    int a, b;
    volatile int *out = 0;
    if (scanf("%d %d", &a, &b) != 2) {
        return 1;
    }
    *out = a + b;
    printf("%d\n", a + b);
    return 0;
}
