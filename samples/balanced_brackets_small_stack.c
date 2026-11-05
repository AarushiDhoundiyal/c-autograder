#include <stdio.h>

char st[100];
int top = 0;

char match(int c) {
    return c == ')' ? '(' : c == ']' ? '[' : '{';
}

/* The stack holds 100 brackets and is never bounds-checked; deeper nesting overflows it. */
int main(void) {
    int c;
    while ((c = getchar()) != EOF) {
        if (c == '(' || c == '[' || c == '{') {
            st[top++] = (char)c;
        } else if (c == ')' || c == ']' || c == '}') {
            if (top == 0 || st[top - 1] != match(c)) {
                printf("NO\n");
                return 0;
            }
            top--;
        }
    }
    printf("%s\n", top == 0 ? "YES" : "NO");
    return 0;
}
