#include <stdio.h>
#include <stdbool.h>

#define MAX_LEN 100000

static char open_brackets[MAX_LEN];
static int depth = 0;

static bool is_open(int ch) {
    return ch == '(' || ch == '[' || ch == '{';
}

static bool is_close(int ch) {
    return ch == ')' || ch == ']' || ch == '}';
}

static char matching_open(int ch) {
    if (ch == ')') {
        return '(';
    }
    return ch == ']' ? '[' : '{';
}

/* Returns true when every closing bracket matches the most recent unmatched opening one. */
static bool brackets_balanced(void) {
    int ch;
    while ((ch = getchar()) != EOF) {
        if (is_open(ch)) {
            if (depth == MAX_LEN) {
                return false;
            }
            open_brackets[depth++] = (char)ch;
        } else if (is_close(ch)) {
            if (depth == 0 || open_brackets[depth - 1] != matching_open(ch)) {
                return false;
            }
            depth--;
        }
    }
    return depth == 0;
}

int main(void) {
    printf("%s\n", brackets_balanced() ? "YES" : "NO");
    return 0;
}
