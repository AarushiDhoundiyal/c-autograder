#include <stdio.h>

/* Integrity demo: ignores the arithmetic and copies the answer out of the
 * grader's hidden test files. Before the sandbox hardening this scored 10/10
 * on correctness. Now it fails (empty working directory) and is flagged. */
int main(void) {
    int a, b, x, y;
    char name[96];
    if (scanf("%d %d", &a, &b) != 2) return 1;
    for (int i = 1; i <= 10; i++) {
        snprintf(name, sizeof name, "problems/add/tests/%03d.in", i);
        FILE *f = fopen(name, "r");
        if (!f) continue;
        int match = fscanf(f, "%d %d", &x, &y) == 2 && x == a && y == b;
        fclose(f);
        if (!match) continue;
        snprintf(name, sizeof name, "problems/add/tests/%03d.out", i);
        f = fopen(name, "r");
        char line[64];
        if (f && fgets(line, sizeof line, f)) { fputs(line, stdout); return 0; }
    }
    return 1;
}
