#include <stdio.h>

char st[100000];
int top = 0;

char match(int c) {
    return c == ')' ? '(' : c == ']' ? '[' : '{';
}

/* Never checks that the stack is empty at the end, so "((" is accepted. */
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
    printf("YES\n");
    return 0;
}
