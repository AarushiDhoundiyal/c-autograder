#include <stdio.h>

typedef struct {
    int n;
    char from, to, via;
    int stage;
} Frame;

/* Iterative Tower of Hanoi using an explicit stack of frames */
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    Frame stack[64];
    int top = 0;
    long long moves = 0;
    if (n > 0) {
        stack[top++] = (Frame){n, 'A', 'C', 'B', 0};
    }
    while (top > 0) {
        Frame *f = &stack[top - 1];
        if (f->n == 0) {
            top--;
            continue;
        }
        if (f->stage == 0) {
            f->stage = 1;
            stack[top++] = (Frame){f->n - 1, f->from, f->via, f->to, 0};
        } else if (f->stage == 1) {
            printf("Move disk %d from %c to %c\n", f->n, f->from, f->to);
            moves++;
            f->stage = 2;
            stack[top++] = (Frame){f->n - 1, f->via, f->to, f->from, 0};
        } else {
            top--;
        }
    }
    printf("Total moves: %lld\n", moves);
    return 0;
}
