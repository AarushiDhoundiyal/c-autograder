#include <stdio.h>

#define MAX_LEN 1000

/**
 * Returns the length of the longest block of identical consecutive characters.
 */
int longest_run(const char *str) {
    if (str[0] == '\0') {
        return 0;
    }
    int longest = 1;
    int current = 1;
    for (int i = 1; str[i] != '\0'; i++) {
        current = (str[i] == str[i - 1]) ? current + 1 : 1;
        if (current > longest) {
            longest = current;
        }
    }
    return longest;
}

int main(void) {
    char str[MAX_LEN + 1];
    if (scanf("%1000s", str) != 1) {
        fprintf(stderr, "Invalid input\n");
        return 1;
    }
    printf("%d\n", longest_run(str));
    return 0;
}
