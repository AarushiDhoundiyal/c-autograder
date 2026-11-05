#include <stdio.h>
#include <stdbool.h>

#define MAX 8

/* Recursively fills `current` with unused numbers in increasing order */
void backtrack(int n, int depth, int current[], bool chosen[]) {
    if (depth == n) {
        for (int i = 0; i < n; i++) {
            printf("%d%c", current[i], i == n - 1 ? '\n' : ' ');
        }
        return;
    }
    for (int value = 1; value <= n; value++) {
        if (chosen[value]) {
            continue;
        }
        chosen[value] = true;
        current[depth] = value;
        backtrack(n, depth + 1, current, chosen);
        chosen[value] = false;
    }
}

int main(void) {
    int n;
    int current[MAX];
    bool chosen[MAX + 1] = {false};
    if (scanf("%d", &n) != 1 || n < 1 || n > MAX) {
        return 1;
    }
    backtrack(n, 0, current, chosen);
    return 0;
}
