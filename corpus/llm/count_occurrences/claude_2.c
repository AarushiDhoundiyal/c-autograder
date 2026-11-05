#include <stdio.h>
#include <stdlib.h>

/**
 * Counts how many elements of arr are equal to target.
 */
int count_occurrences(const int *arr, int n, int target) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) {
            count++;
        }
    }
    return count;
}

int main(void) {
    int n, target;
    if (scanf("%d %d", &n, &target) != 2 || n < 1) {
        fprintf(stderr, "Invalid input\n");
        return 1;
    }
    int *arr = malloc((size_t)n * sizeof(int));
    if (arr == NULL) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &arr[i]) != 1) {
            free(arr);
            return 1;
        }
    }
    printf("%d\n", count_occurrences(arr, n, target));
    free(arr);
    return 0;
}
