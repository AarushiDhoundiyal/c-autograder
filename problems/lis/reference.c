/* Trusted reference solution for lis: patience sorting with binary search, O(n log n). */
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        return 1;
    }
    int *tail = malloc(sizeof *tail * (size_t)(n > 0 ? n : 1));
    if (!tail) {
        return 1;
    }
    int len = 0;
    for (int i = 0; i < n; i++) {
        int x;
        if (scanf("%d", &x) != 1) {
            break;
        }
        int lo = 0, hi = len;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (tail[mid] < x) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        tail[lo] = x;
        if (lo == len) {
            len++;
        }
    }
    printf("%d\n", len);
    free(tail);
    return 0;
}
