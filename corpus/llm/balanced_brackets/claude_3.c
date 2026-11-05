#include <stdio.h>
#include <string.h>

#define MAX_LEN 100001

static char text[MAX_LEN];

/* Reads the whole input, then checks it with an index-based stack */
int main(void) {
    size_t len = fread(text, 1, MAX_LEN - 1, stdin);
    text[len] = '\0';

    char stack[MAX_LEN];
    int depth = 0;
    const char *opens = "([{";
    const char *closes = ")]}";

    for (size_t i = 0; i < len; i++) {
        const char *o = strchr(opens, text[i]);
        const char *c = strchr(closes, text[i]);
        if (text[i] != '\0' && o != NULL) {
            stack[depth++] = text[i];
        } else if (text[i] != '\0' && c != NULL) {
            if (depth == 0 || stack[depth - 1] != opens[c - closes]) {
                puts("NO");
                return 0;
            }
            depth--;
        }
    }
    puts(depth == 0 ? "YES" : "NO");
    return 0;
}
