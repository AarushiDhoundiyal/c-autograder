#include <stdio.h>
#include <stdlib.h>

static long long add(long long a, long long b) { return a + b; }

int main(void) {
    int a, b;
    long long *result = malloc(sizeof *result);
    if (scanf("%d %d", &a, &b) != 2 || !result) {
        return 1;
    }
    *result = add(a, b);
    printf("%lld\n", *result);
    return 0;
}
