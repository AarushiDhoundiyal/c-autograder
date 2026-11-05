#include <stdio.h>
static int parent[121], rankv[121];
static int find(int x) { return parent[x] == x ? x : (parent[x] = find(parent[x])); }
static void unite(int a, int b) {
    a = find(a); b = find(b);
    if (a == b) return;
    if (rankv[a] < rankv[b]) { int tmp = a; a = b; b = tmp; }
    parent[b] = a;
    if (rankv[a] == rankv[b]) ++rankv[a];
}
int main(void) {
    int n,m; if (scanf("%d%d", &n,&m) != 2 || n < 1 || n > 120) return 1;
    for (int i = 1; i <= n; ++i) parent[i] = i;
    for (int i = 0; i < m; ++i) {
        int a,b; if (scanf("%d%d", &a,&b) != 2) return 1;
        unite(a,b);
    }
    int c = 0;
    for (int i = 1; i <= n; ++i) if (find(i) == i) ++c;
    printf("%d\n", c);
    return 0;
}
