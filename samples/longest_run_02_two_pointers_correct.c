#include <stdio.h>
#include <string.h>
static int longest(const char *s) {
    int length = (int)strlen(s), best = 0;
    for (int left = 0; left < length;) {
        int right = left + 1;
        while (right < length && s[right] == s[left]) ++right;
        if (right - left > best) best = right - left;
        left = right;
    }
    return best;
}
int main(void) {
    char word[1001];
    if (scanf("%1000s", word) != 1) return 1;
    printf("%d\n", longest(word));
    return 0;
}
