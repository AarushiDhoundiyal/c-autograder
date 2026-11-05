#include <stdio.h>
#include <string.h>

int main() {
    char s[1001];
    scanf("%s", s);

    int maxLen = 1;
    int currentLen = 1;

    // Walk through the string and track the current streak
    for (int i = 1; i < strlen(s); i++) {
        if (s[i] == s[i - 1]) {
            currentLen++;
        } else {
            currentLen = 1;
        }
        if (currentLen > maxLen) {
            maxLen = currentLen;
        }
    }

    printf("%d\n", maxLen);
    return 0;
}
