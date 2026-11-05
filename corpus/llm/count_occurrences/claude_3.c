#include <stdio.h>

#define OFFSET 10000
#define RANGE 20001

static int frequency[RANGE];

/* Builds a frequency table, then looks up the target in O(1) */
int main(void) {
    int n, k;
    if (scanf("%d %d", &n, &k) != 2) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        int value;
        if (scanf("%d", &value) != 1) {
            return 1;
        }
        frequency[value + OFFSET]++;
    }
    printf("%d\n", frequency[k + OFFSET]);
    return 0;
}
