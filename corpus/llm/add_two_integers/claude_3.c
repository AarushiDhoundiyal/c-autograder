#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>

int main(void) {
    int32_t first, second;

    /* Read the two numbers */
    if (scanf("%" SCNd32 " %" SCNd32, &first, &second) != 2) {
        return 1;
    }

    /* Widen before adding to avoid signed overflow */
    int64_t sum = (int64_t)first + (int64_t)second;
    printf("%" PRId64 "\n", sum);

    return 0;
}
