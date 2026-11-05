/* Trusted reference solution for balanced_brackets: an explicit stack of open brackets. */
#include <stdio.h>

#define MAX_LEN 100000

static char stack[MAX_LEN + 1];

int main(void) {
    int top = 0, ok = 1, ch;
    while ((ch = getchar()) != EOF) {
        if (ch == '(' || ch == '[' || ch == '{') {
            if (top < MAX_LEN) {
                stack[top++] = (char)ch;
            }
        } else if (ch == ')' || ch == ']' || ch == '}') {
            char want = ch == ')' ? '(' : ch == ']' ? '[' : '{';
            if (top == 0 || stack[top - 1] != want) {
                ok = 0;
                break;
            }
            top--;
        }
    }
    puts(ok && top == 0 ? "YES" : "NO");
    return 0;
}
