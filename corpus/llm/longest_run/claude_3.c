#include <stdio.h>
#include <ctype.h>

/* Reads the string character by character, so no buffer is needed */
int main(void) {
    int ch, previous = EOF;
    int run = 0, best = 0;
    while ((ch = getchar()) != EOF && !isspace(ch)) {
        run = (ch == previous) ? run + 1 : 1;
        if (run > best) {
            best = run;
        }
        previous = ch;
    }
    printf("%d\n", best);
    return 0;
}
