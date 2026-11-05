#include <stdio.h>
#include <stdbool.h>

#define MAX_N 8

static int length;
static int current[MAX_N];
static bool in_use[MAX_N + 1];

static void print_permutation(void) {
    for (int i = 0; i < length; i++) {
        printf(i == 0 ? "%d" : " %d", current[i]);
    }
    printf("\n");
}

/* Fill position `pos` with each unused value in increasing order, then recurse. */
static void generate(int pos) {
    if (pos == length) {
        print_permutation();
        return;
    }
    for (int value = 1; value <= length; value++) {
        if (in_use[value]) {
            continue;
        }
        in_use[value] = true;
        current[pos] = value;
        generate(pos + 1);
        in_use[value] = false;
    }
}

int main(void) {
    if (scanf("%d", &length) != 1 || length < 1 || length > MAX_N) {
        return 1;
    }
    generate(0);
    return 0;
}
