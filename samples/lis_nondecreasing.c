#include <stdio.h>

int a[5000], len[5000];

/* Uses <= instead of <, so equal values are counted as increasing. */
int lis(int n) {
    int best = 0;
    for (int i = 0; i < n; i++) {
        len[i] = 1;
        for (int j = 0; j < i; j++) {
            if (a[j] <= a[i] && len[j] + 1 > len[i]) {
                len[i] = len[j] + 1;
            }
        }
        if (len[i] > best) {
            best = len[i];
        }
    }
    return best;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &a[i]) != 1) {
            return 1;
        }
    }
    printf("%d\n", lis(n));
    return 0;
}
