/* Trusted reference solution for graph_components (from the five-assignment test pack). */
#include <stdio.h>
#define MAXV 120
static unsigned char adj[MAXV + 1][MAXV + 1], seen[MAXV + 1];
static void dfs(int u, int n) {
    seen[u] = 1;
    for (int v = 1; v <= n; ++v) if (adj[u][v] && !seen[v]) dfs(v, n);
}
int main(void) {
    int n, m;
    if (scanf("%d%d", &n, &m) != 2 || n < 1 || n > MAXV || m < 0 || m > n*(n-1)/2) return 1;
    for (int i = 0; i < m; ++i) {
        int u,v; if (scanf("%d%d", &u, &v) != 2 || u < 1 || u > n || v < 1 || v > n || u == v) return 1;
        adj[u][v] = adj[v][u] = 1;
    }
    int components = 0;
    for (int u = 1; u <= n; ++u) if (!seen[u]) { components++; dfs(u, n); }
    printf("%d\n", components);
    return 0;
}
