#include <stdio.h>
#include <stdlib.h>

struct node {
    int value;
    struct node *next;
};

struct node *reverse(struct node *head) {
    struct node *prev = NULL;
    while (head) {
        struct node *next = head->next;
        head->next = prev;
        prev = head;
        head = next;
    }
    return prev;
}

/* Correct output, but the nodes are never freed. */
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
    return 0;
}
