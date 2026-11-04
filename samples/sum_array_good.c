#include <stdio.h>

/* Sum n integers read from standard input (64-bit accumulator avoids overflow). */
static long long read_and_sum(int n) {
    long long total = 0;
    for (int i = 0; i < n; i++) {
        int value;
        if (scanf("%d", &value) != 1) {
            break;
        }
        total += value;
    }
    return total;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    printf("%lld\n", read_and_sum(n));
    return 0;
}
