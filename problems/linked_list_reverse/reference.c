/* Trusted reference solution for linked_list_reverse (from the five-assignment test pack). */
#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int value; struct Node *next; } Node;
int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0 || n > 100) return 1;
    Node *head = NULL;
    for (int i = 0, x; i < n; ++i) {
        if (scanf("%d", &x) != 1) return 1;
        Node *node = malloc(sizeof *node);
        if (!node) return 1;
        node->value = x;
        node->next = head;
        head = node;
    }
    if (!head) puts("EMPTY");
    else {
        for (Node *p = head; p; p = p->next) printf("%d%s", p->value, p->next ? " " : "\n");
    }
    while (head) { Node *next = head->next; free(head); head = next; }
    return 0;
}
