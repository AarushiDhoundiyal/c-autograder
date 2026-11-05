#include <stdio.h>
#include <string.h>
int main(void) {
    char s[1001];
    if (scanf("%1000s", s) != 1) return 1;
    int n = (int)strlen(s), best = 0;
    for (int i = 0; i < n; ++i) {
        int count = 0;
        for (int j = i; j < n; ++j) {
            if (s[j] != s[i]) break;
            ++count;
        }
        if (count > best) best = count;
    }
    printf("%d\n", best);
    return 0;
}
