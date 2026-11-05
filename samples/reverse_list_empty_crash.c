#include <stdio.h>
#include <stdlib.h>

struct node {
    int value;
    struct node *next;
};

/* Assumes the list has at least one node: an empty list dereferences NULL. */
struct node *reverse(struct node *head) {
    struct node *prev = head;
    struct node *cur = head->next;
    prev->next = NULL;
    while (cur) {
        struct node *next = cur->next;
        cur->next = prev;
        prev = cur;
        cur = next;
    }
    return prev;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    struct node *head = NULL, *tail = NULL;
    for (int i = 0; i < n; i++) {
        struct node *nd = malloc(sizeof *nd);
        if (!nd || scanf("%d", &nd->value) != 1) {
            return 1;
        }
        nd->next = NULL;
        if (tail) {
            tail->next = nd;
        } else {
            head = nd;
        }
        tail = nd;
    }
    head = reverse(head);
    for (struct node *p = head; p; p = p->next) {
        printf("%d ", p->value);
    }
    printf("\n");
    while (head) {
        struct node *next = head->next;
        free(head);
        head = next;
    }
    return 0;
}
