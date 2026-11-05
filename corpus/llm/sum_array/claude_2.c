#include <stdio.h>

/**
 * Reads `count` integers from standard input and returns their sum.
 * A long long accumulator is used so the sum does not overflow.
 */
long long read_and_sum(int count) {
    long long total = 0;
    for (int i = 0; i < count; i++) {
        int value;
        if (scanf("%d", &value) != 1) {
            break;
        }
        total += value;
    }
    return total;
}

int main(void) {
    int count;
    if (scanf("%d", &count) != 1 || count < 0) {
        fprintf(stderr, "Invalid input\n");
        return 1;
    }
    printf("%lld\n", read_and_sum(count));
    return 0;
}
