#include <stdio.h>

int main() {
    int n, k;
    int count = 0;

    // Read the size of the array and the target value
    scanf("%d %d", &n, &k);

    // Read each element and count matches
    for (int i = 0; i < n; i++) {
        int x;
        scanf("%d", &x);
        if (x == k) {
            count++;
        }
    }

    // Print the number of occurrences
    printf("%d\n", count);
    return 0;
}
