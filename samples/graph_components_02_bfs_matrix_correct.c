#include <stdio.h>
static unsigned char matrix[121][121], used[121];
int main(void) {
    int n,m; if (scanf("%d%d", &n, &m) != 2 || n < 1 || n > 120) return 1;
    for (int i = 0; i < m; ++i) {
        int u,v; if (scanf("%d%d", &u,&v) != 2) return 1;
        matrix[u][v] = matrix[v][u] = 1;
    }
    int components = 0, queue[121];
    for (int start = 1; start <= n; ++start) {
        if (used[start]) continue;
        ++components;
        int front = 0, back = 0;
        used[start] = 1; queue[back++] = start;
        while (front < back) {
            int x = queue[front++];
            for (int y = 1; y <= n; ++y) if (matrix[x][y] && !used[y]) {
                used[y] = 1; queue[back++] = y;
            }
        }
    }
    printf("%d\n", components);
    return 0;
}
