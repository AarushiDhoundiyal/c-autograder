#include <stdio.h>
int main(void) {
    int n;
    long long s = 0;
    scanf("%d", &n);
    for (int i = 0; i < n - 1; i++) {   /* bug: skips the last element */
        int v;
        scanf("%d", &v);
        s += v;
    }
    printf("%lld\n", s);
    return 0;
}
