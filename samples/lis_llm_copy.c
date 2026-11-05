#include <stdio.h>
#include <stdlib.h>

/* Copied from an LLM answer, with renamed variables and rewritten comments. */
int find_slot(const int *ends, int count, int key) {
    int lo = 0, hi = count;
    while (lo < hi) {
        int middle = lo + (hi - lo) / 2;
        if (ends[middle] < key) {
            lo = middle + 1;
        } else {
            hi = middle;
        }
    }
    return lo;
}

int longest_run(const int *data, int total) {
    int *ends = malloc((size_t)(total > 0 ? total : 1) * sizeof(int));
    int count = 0;
    for (int k = 0; k < total; k++) {
        int slot = find_slot(ends, count, data[k]);
        ends[slot] = data[k];
        if (slot == count) {
            count++;
        }
    }
    free(ends);
    return count;
}

int main(void) {
    int total;
    if (scanf("%d", &total) != 1 || total < 0) {
        return 1;
    }
    int *data = malloc((size_t)(total > 0 ? total : 1) * sizeof(int));
    for (int k = 0; k < total; k++) {
        scanf("%d", &data[k]);
    }
    printf("%d\n", longest_run(data, total));
    free(data);
    return 0;
}
