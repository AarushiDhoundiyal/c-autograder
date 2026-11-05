#include <stdio.h>
/* Copied from a tutorial website, with renamed variables. */
long long total(long long p, long long q) { return p + q; }
int main() {
    long long first, second;
    scanf("%lld%lld", &first, &second);
    printf("%lld\n", total(first, second));
    return 0;
}
