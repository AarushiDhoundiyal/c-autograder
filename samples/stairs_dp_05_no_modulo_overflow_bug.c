#include <stdio.h>
int main(void) {
    int n; if (scanf("%d", &n) != 1 || n < 0 || n > 1000) return 1;
    long long a = 1, b = 1;
    for (int i = 2; i <= n; ++i) {
        long long next = a + b; /* BUG: signed overflow; modulo omitted */
        a = b; b = next;
    }
    printf("%lld\n", b);
    return 0;
}
