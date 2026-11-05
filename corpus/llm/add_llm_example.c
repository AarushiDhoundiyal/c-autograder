#include <stdio.h>

/* Example of an LLM-style solution kept in the corpus (replace with real ones). */
int main(void) {
    long long first, second;
    if (scanf("%lld %lld", &first, &second) != 2) {
        return 1;
    }
    printf("%lld\n", first + second);
    return 0;
}
