/* Trusted reference solution for longest_run (from the five-assignment test pack). */
#include <stdio.h>
#include <string.h>
int main(void) {
    char s[1001];
    if (scanf("%1000s", s) != 1) return 1;
    int best = 1, run = 1;
    for (size_t i = 1; s[i] != '\0'; ++i) {
        if (s[i] == s[i - 1]) run++;
        else run = 1;
        if (run > best) best = run;
    }
    printf("%d\n", best);
    return 0;
}
