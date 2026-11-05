#include <stdio.h>
static char g[121][121], visited[121];
static void dfs(int x, int n) {
    visited[x] = 1;
    for (int y = 1; y <= n; ++y) if (g[x][y] && !visited[y]) dfs(y,n);
}
int main(void) {
    int n,m; if (scanf("%d%d", &n,&m) != 2 || n < 1 || n > 120) return 1;
    for (int i = 0; i < m; ++i) {
        int a,b; if (scanf("%d%d", &a,&b) != 2) return 1;
        g[a][b] = 1; /* BUG: missing reverse edge in undirected graph */
    }
    int count = 0;
    for (int v = 1; v <= n; ++v) if (!visited[v]) { dfs(v,n); ++count; }
    printf("%d\n", count);
    return 0;
}
