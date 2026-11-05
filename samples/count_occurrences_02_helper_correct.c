#include <stdio.h>
static int occurrences(const int *values, int n, int t) {
    int total = 0;
    for (int k = 0; k < n; ++k) total += values[k] == t;
    return total;
}
int main(void) {
    int n, t, values[1000];
    if (scanf("%d%d", &n, &t) != 2 || n < 1 || n > 1000) return 1;
    for (int i = 0; i < n; ++i) if (scanf("%d", &values[i]) != 1) return 1;
    printf("%d\n", occurrences(values, n, t));
    return 0;
}
