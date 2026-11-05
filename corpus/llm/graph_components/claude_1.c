#include <stdio.h>

int adj[121][121];
int visited[121];
int n, m;

// Depth-first search from vertex v
void dfs(int v) {
    visited[v] = 1;
    for (int u = 1; u <= n; u++) {
        if (adj[v][u] && !visited[u]) {
            dfs(u);
        }
    }
}

int main() {
    scanf("%d %d", &n, &m);

    // Read the undirected edges
    for (int i = 0; i < m; i++) {
        int u, v;
        scanf("%d %d", &u, &v);
        adj[u][v] = 1;
        adj[v][u] = 1;
    }

    // Count connected components
    int components = 0;
    for (int i = 1; i <= n; i++) {
        if (!visited[i]) {
            dfs(i);
            components++;
        }
    }

    printf("%d\n", components);
    return 0;
}
