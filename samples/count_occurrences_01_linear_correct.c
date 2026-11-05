#include <stdio.h>
int main(void) {
    int n, t, a[1000], answer = 0;
    if (scanf("%d %d", &n, &t) != 2 || n < 1 || n > 1000) return 1;
    for (int i = 0; i < n; i++) if (scanf("%d", &a[i]) != 1) return 1;
    for (int i = 0; i < n; i++) if (a[i] == t) answer++;
    printf("%d\n", answer);
    return 0;
}
