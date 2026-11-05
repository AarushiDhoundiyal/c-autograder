#include <stdio.h>
#include <stdbool.h>

static void swap(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

static void reverse(int *arr, int start, int end) {
    while (start < end) {
        swap(&arr[start], &arr[end]);
        start++;
        end--;
    }
}

/**
 * Rearranges arr into the next lexicographic permutation.
 * Returns false when arr is already the last permutation.
 */
static bool next_permutation(int *arr, int n) {
    int i = n - 2;
    while (i >= 0 && arr[i] >= arr[i + 1]) {
        i--;
    }
    if (i < 0) {
        return false;
    }
    int j = n - 1;
    while (arr[j] <= arr[i]) {
        j--;
    }
    swap(&arr[i], &arr[j]);
    reverse(arr, i + 1, n - 1);
    return true;
}

static void print_array(const int *arr, int n) {
    for (int i = 0; i < n; i++) {
        printf(i == 0 ? "%d" : " %d", arr[i]);
    }
    printf("\n");
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 1 || n > 8) {
        return 1;
    }
    int arr[8];
    for (int i = 0; i < n; i++) {
        arr[i] = i + 1;
    }
    do {
        print_array(arr, n);
    } while (next_permutation(arr, n));
    return 0;
}
