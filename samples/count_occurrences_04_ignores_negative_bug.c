#include <stdio.h>
int main(void) {
    int n, target, x, count = 0;
    if (scanf("%d%d", &n, &target) != 2 || n < 1 || n > 1000) return 1;
    for (int i = 0; i < n; ++i) {
        if (scanf("%d", &x) != 1) return 1;
        if (x >= 0 && x == target) count++; /* BUG: ignores negative targets */
    }
    printf("%d\n", count);
    return 0;
}
