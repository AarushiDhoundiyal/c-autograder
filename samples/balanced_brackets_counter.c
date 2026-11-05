#include <stdio.h>

/* Counts each bracket type separately, so wrong nesting such as "([)]" is accepted. */
int main(void) {
    int round = 0, square = 0, curly = 0, ok = 1, ch;
    while ((ch = getchar()) != EOF) {
        if (ch == '(') round++;
        if (ch == ')') round--;
        if (ch == '[') square++;
        if (ch == ']') square--;
        if (ch == '{') curly++;
        if (ch == '}') curly--;
        if (round < 0 || square < 0 || curly < 0) {
            ok = 0;
        }
    }
    if (round != 0 || square != 0 || curly != 0) {
        ok = 0;
    }
    printf("%s\n", ok ? "YES" : "NO");
    return 0;
}
