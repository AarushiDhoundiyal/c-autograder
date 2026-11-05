#include <stdio.h>

#define MOD 1000000007

int main() {
    int n;
    scanf("%d", &n);

    // ways[i] = ways[i-1] + ways[i-2], with ways[0] = ways[1] = 1
    long long prev2 = 1, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        long long curr = (prev1 + prev2) % MOD;
        prev2 = prev1;
        prev1 = curr;
    }

    printf("%lld\n", prev1);
    return 0;
}
