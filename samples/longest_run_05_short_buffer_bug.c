#include <stdio.h>
int main(void) {
    char word[16]; /* BUG: reads up to 1000 characters into 16 bytes */
    if (scanf("%1000s", word) != 1) return 1;
    int current = 1, answer = 1;
    for (int i = 1; word[i]; ++i) {
        current = word[i] == word[i-1] ? current+1 : 1;
        if (current > answer) answer = current;
    }
    printf("%d\n", answer);
    return 0;
}
