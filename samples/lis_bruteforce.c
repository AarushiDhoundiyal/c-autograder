#include <stdio.h>
#include <limits.h>

int a[5000];
int n;

/* Tries every subsequence by including or skipping each element: correct but O(2^n). */
int longest(int i, long long last) {
    if (i == n) {
        return 0;
    }
    int skip = longest(i + 1, last);
    if (a[i] > last) {
        int take = 1 + longest(i + 1, a[i]);
        if (take > skip) {
            return take;
        }
    }
    return skip;
}

int main(void) {
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &a[i]) != 1) {
            return 1;
        }
    }
    printf("%d\n", longest(0, (long long)INT_MIN - 1));
    return 0;
}
