#include <stdio.h>
#define MOD 1000000007LL
int main(void) {
    int n; if (scanf("%d", &n) != 1 || n < 0 || n > 1000) return 1;
    if (n == 0) { puts("0"); return 0; } /* BUG: one empty way exists */
    long long a = 1, b = 1;
    for (int k = 2; k <= n; ++k) { long long t=(a+b)%MOD; a=b; b=t; }
    printf("%lld\n", b);
    return 0;
}
