/* Trusted reference solution for reverse_list: build, reverse in place, print, free. */
#include <stdio.h>
#include <stdlib.h>

struct node {
    int value;
    struct node *next;
};

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        return 1;
    }
    struct node *head = NULL, *tail = NULL;
    for (int i = 0; i < n; i++) {
        int x;
        if (scanf("%d", &x) != 1) {
            break;
        }
        struct node *nd = malloc(sizeof *nd);
        if (!nd) {
            return 1;
        }
        nd->value = x;
        nd->next = NULL;
        if (tail) {
            tail->next = nd;
        } else {
            head = nd;
        }
        tail = nd;
    }
    struct node *prev = NULL;
    while (head) {
        struct node *next = head->next;
        head->next = prev;
        prev = head;
        head = next;
    }
    for (struct node *p = prev; p; p = p->next) {
        printf(p == prev ? "%d" : " %d", p->value);
    }
    putchar('\n');
    while (prev) {
        struct node *next = prev->next;
        free(prev);
        prev = next;
    }
    return 0;
}
