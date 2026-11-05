#include <stdio.h>

#define MAX_N 5000

static int seq[MAX_N];
static int ending_here[MAX_N];

/* ending_here[i] = length of the longest increasing subsequence that ends at seq[i]. */
static int longest_increasing(int n) {
    int best = 0;
    for (int i = 0; i < n; i++) {
        ending_here[i] = 1;
        for (int j = 0; j < i; j++) {
            if (seq[j] < seq[i] && ending_here[j] + 1 > ending_here[i]) {
                ending_here[i] = ending_here[j] + 1;
            }
        }
        if (ending_here[i] > best) {
            best = ending_here[i];
        }
    }
    return best;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0 || n > MAX_N) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &seq[i]) != 1) {
            return 1;
        }
    }
    printf("%d\n", longest_increasing(n));
    return 0;
}
