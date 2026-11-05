#include <stdio.h>
int main(void) {
    char s[1001];
    if (scanf("%1000s", s) != 1) return 1;
    int ans = 1, current = 1;
    for (int i = 1; s[i]; ++i) {
        current = (s[i] == s[i - 1]) ? current + 1 : 1;
        if (current > ans) ans = current;
    }
    printf("%d\n", ans);
    return 0;
}
