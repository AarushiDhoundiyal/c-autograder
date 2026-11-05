#include <stdio.h>
#include <stdlib.h>

/**
 * Returns the index of the first element in tails[0..len) that is >= target.
 */
int lower_bound(const int *tails, int len, int target) {
    int low = 0, high = len;
    while (low < high) {
        int mid = low + (high - low) / 2;
        if (tails[mid] < target) {
            low = mid + 1;
        } else {
            high = mid;
        }
    }
    return low;
}

/**
 * Computes the length of the longest strictly increasing subsequence
 * in O(n log n) using the patience sorting technique.
 */
int longest_increasing_subsequence(const int *nums, int n) {
    int *tails = malloc((size_t)(n > 0 ? n : 1) * sizeof(int));
    int length = 0;
    for (int i = 0; i < n; i++) {
        int pos = lower_bound(tails, length, nums[i]);
        tails[pos] = nums[i];
        if (pos == length) {
            length++;
        }
    }
    free(tails);
    return length;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        return 1;
    }
    int *nums = malloc((size_t)(n > 0 ? n : 1) * sizeof(int));
    for (int i = 0; i < n; i++) {
        scanf("%d", &nums[i]);
    }
    printf("%d\n", longest_increasing_subsequence(nums, n));
    free(nums);
    return 0;
}
