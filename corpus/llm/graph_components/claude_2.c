#include <stdio.h>

#define MAX_N 120

static int parent[MAX_N + 1];
static int size_of[MAX_N + 1];

/** Finds the root of x with path compression. */
static int find_root(int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

/** Merges the sets of a and b; returns 1 if they were different. */
static int union_sets(int a, int b) {
    int ra = find_root(a), rb = find_root(b);
    if (ra == rb) {
        return 0;
    }
    if (size_of[ra] < size_of[rb]) {
        int tmp = ra;
        ra = rb;
        rb = tmp;
    }
    parent[rb] = ra;
    size_of[ra] += size_of[rb];
    return 1;
}

int main(void) {
    int n, m;
    if (scanf("%d %d", &n, &m) != 2 || n < 1 || n > MAX_N) {
        return 1;
    }
    for (int v = 1; v <= n; v++) {
        parent[v] = v;
        size_of[v] = 1;
    }
    int components = n;
    for (int i = 0; i < m; i++) {
        int u, v;
        if (scanf("%d %d", &u, &v) != 2) {
            return 1;
        }
        components -= union_sets(u, v);
    }
    printf("%d\n", components);
    return 0;
}
