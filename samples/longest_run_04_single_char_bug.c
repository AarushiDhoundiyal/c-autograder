#include <stdio.h>
int main(void) {
    char text[1001];
    if (scanf("%1000s", text) != 1) return 1;
    int best = 0, run = 0; /* BUG: singleton streak is never counted */
    for (int i = 1; text[i]; ++i) {
        if (text[i] == text[i-1]) ++run;
        else run = 0;
        if (run > best) best = run;
    }
    printf("%d\n", best);
    return 0;
}
