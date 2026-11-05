#include <stdio.h>
static char adj[121][121], visited[121];
static void dfs(int u, int n) {
    visited[u] = 1;
    for (int v = 1; v <= n; ++v) if (adj[u][v] && !visited[v]) dfs(v,n);
}
int main(void) {
    int n,m; if (scanf("%d%d", &n,&m) != 2 || n < 1 || n > 120) return 1;
    for (int k=0; k<m; ++k) {
        int a,b; if (scanf("%d%d", &a,&b) != 2) return 1;
        adj[a][b] = adj[b][a] = 1;
    }
    int count = 0;
    for (int u = 1; u <= n; ++u) {
        int has_edge = 0;
        for (int v = 1; v <= n; ++v) if (adj[u][v]) has_edge = 1;
        if (has_edge && !visited[u]) { ++count; dfs(u,n); } /* BUG: ignores isolated vertices */
    }
    printf("%d\n", count);
    return 0;
}
