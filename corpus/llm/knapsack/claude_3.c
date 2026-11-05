#include <stdio.h>
#include <string.h>

#define MAX_ITEMS 100
#define MAX_CAP 10000

int weight[MAX_ITEMS], value[MAX_ITEMS];
long long memo[MAX_ITEMS + 1][MAX_CAP + 1];
int n;

/* Top-down recursion with memoisation: best value from item i onwards */
long long solve(int i, int cap) {
    if (i == n) {
        return 0;
    }
    if (memo[i][cap] != -1) {
        return memo[i][cap];
    }
    long long skip = solve(i + 1, cap);
    long long take = 0;
    if (weight[i] <= cap) {
        take = value[i] + solve(i + 1, cap - weight[i]);
    }
    memo[i][cap] = skip > take ? skip : take;
    return memo[i][cap];
}

int main(void) {
    int cap;
    if (scanf("%d %d", &n, &cap) != 2) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        scanf("%d %d", &weight[i], &value[i]);
    }
    memset(memo, -1, sizeof(memo));
    printf("%lld\n", solve(0, cap));
    return 0;
}
