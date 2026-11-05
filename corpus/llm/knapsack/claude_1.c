#include <stdio.h>

int dp[10001];

int main() {
    int n, W;
    scanf("%d %d", &n, &W);

    // 0/1 knapsack: iterate capacity backwards so each item is used once
    for (int i = 0; i < n; i++) {
        int w, v;
        scanf("%d %d", &w, &v);
        for (int c = W; c >= w; c--) {
            if (dp[c - w] + v > dp[c]) {
                dp[c] = dp[c - w] + v;
            }
        }
    }

    printf("%d\n", dp[W]);
    return 0;
}
