#include <stdio.h>

int n, a[8];

void swap(int *x, int *y) {
    int t = *x;
    *x = *y;
    *y = t;
}

/* The swap method prints every permutation once, but not in lexicographic order. */
void permute(int k) {
    if (k == n) {
        for (int i = 0; i < n; i++) {
            printf("%d ", a[i]);
        }
        printf("\n");
        return;
    }
    for (int i = k; i < n; i++) {
        swap(&a[k], &a[i]);
        permute(k + 1);
        swap(&a[k], &a[i]);
    }
}

int main(void) {
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        a[i] = i + 1;
    }
    permute(0);
    return 0;
}
