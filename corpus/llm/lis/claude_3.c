#include <stdio.h>

#define MAXN 5000

static int seq[MAXN];
static int best_len[MAXN];

/* Length of the longest increasing subsequence that ends at index i */
static int lis_ending_at(int i) {
    int best = 1;
    for (int j = 0; j < i; j++) {
        if (seq[j] < seq[i] && best_len[j] + 1 > best) {
            best = best_len[j] + 1;
        }
    }
    return best;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    for (int i = 0; i < n; i++) {
        scanf("%d", &seq[i]);
    }
    int answer = 0;
    for (int i = 0; i < n; i++) {
        best_len[i] = lis_ending_at(i);
        if (best_len[i] > answer) {
            answer = best_len[i];
        }
    }
    printf("%d\n", answer);
    return 0;
}
