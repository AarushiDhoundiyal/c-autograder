#include <stdio.h>

char stack[100000];
int top = -1;

int main() {
    int ch;
    int balanced = 1;

    // Read the input character by character
    while ((ch = getchar()) != EOF) {
        if (ch == '(' || ch == '[' || ch == '{') {
            stack[++top] = ch;  // push opening bracket
        } else if (ch == ')' || ch == ']' || ch == '}') {
            if (top == -1) {
                balanced = 0;
                break;
            }
            char open = stack[top--];  // pop
            if ((ch == ')' && open != '(') ||
                (ch == ']' && open != '[') ||
                (ch == '}' && open != '{')) {
                balanced = 0;
                break;
            }
        }
    }

    if (top != -1) {
        balanced = 0;
    }

    printf("%s\n", balanced ? "YES" : "NO");
    return 0;
}
