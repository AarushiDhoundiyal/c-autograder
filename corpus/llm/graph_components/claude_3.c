#include <stdio.h>
#include <stdbool.h>

#define MAXV 121

static bool edge[MAXV][MAXV];
static bool seen[MAXV];

/* Breadth-first search with an explicit queue */
static void bfs(int start, int n) {
    int queue[MAXV];
    int head = 0, tail = 0;
    queue[tail++] = start;
    seen[start] = true;
    while (head < tail) {
        int v = queue[head++];
        for (int u = 1; u <= n; u++) {
            if (edge[v][u] && !seen[u]) {
                seen[u] = true;
                queue[tail++] = u;
            }
        }
    }
}

int main(void) {
    int n, m;
    if (scanf("%d %d", &n, &m) != 2) {
        return 1;
    }
    while (m-- > 0) {
        int a, b;
        if (scanf("%d %d", &a, &b) != 2) {
            return 1;
        }
        edge[a][b] = edge[b][a] = true;
    }
    int count = 0;
    for (int v = 1; v <= n; v++) {
        if (!seen[v]) {
            bfs(v, n);
            count++;
        }
    }
    printf("%d\n", count);
    return 0;
}
