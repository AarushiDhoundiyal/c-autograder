#include <stdio.h>
long long sum(long long x, long long y) { return x + y; }
int main() {
    long long a, b;
    scanf("%lld%lld", &a, &b);
    printf("%lld\n", sum(a, b));
    return 0;
}
