#include <stdio.h>
static char g[121][121], seen[121];
static void walk(int u, int n) {
    seen[u] = 1;
    for (int v = 1; v <= n; ++v) if (g[u][v] && !seen[v]) walk(v, n);
}
int main(void) {
    int n,m; if (scanf("%d%d", &n, &m) != 2 || n < 1 || n > 120) return 1;
    for (int k = 0; k < m; ++k) {
        int a,b; if (scanf("%d%d", &a,&b) != 2) return 1;
        g[a][b] = g[b][a] = 1;
    }
    int count = 0;
    for (int i = 1; i <= n; ++i) if (!seen[i]) { ++count; walk(i,n); }
    printf("%d\n", count);
    return 0;
}
