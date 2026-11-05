#include <stdio.h>

int n;
int perm[8];
int used[9];

// Build permutations position by position in lexicographic order
void generate(int pos) {
    if (pos == n) {
        for (int i = 0; i < n; i++) {
            printf("%d", perm[i]);
            if (i < n - 1) printf(" ");
        }
        printf("\n");
        return;
    }
    for (int num = 1; num <= n; num++) {
        if (!used[num]) {
            used[num] = 1;
            perm[pos] = num;
            generate(pos + 1);
            used[num] = 0;
        }
    }
}

int main() {
    scanf("%d", &n);
    generate(0);
    return 0;
}
