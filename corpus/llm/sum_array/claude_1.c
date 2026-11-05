#include <stdio.h>

int main() {
    int n;
    long long sum = 0;

    // Read the number of elements
    scanf("%d", &n);

    // Read each element and add it to the sum
    for (int i = 0; i < n; i++) {
        int x;
        scanf("%d", &x);
        sum += x;
    }

    // Print the total
    printf("%lld\n", sum);
    return 0;
}
