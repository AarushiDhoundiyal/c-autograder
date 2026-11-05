#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int data; struct Node *next; } Node;
static Node *reverse(Node *h) {
    if (!h || !h->next) return h;
    Node *newhead = reverse(h->next);
    h->next->next = h;
    h->next = NULL;
    return newhead;
}
int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0 || n > 100) return 1;
    Node *head = NULL;
    for (int i = 0; i < n; ++i) {
        int value; if (scanf("%d", &value) != 1) return 1;
        Node *p = malloc(sizeof *p); if (!p) return 1;
        p->data = value; p->next = head; head = p;
    }
    /* The list was prepended, so reverse restores input order, then output from tail. */
    head = reverse(head);
    if (!head) puts("EMPTY");
    else {
        /* Reverse it again to output the required reverse order. */
        head = reverse(head);
        for (Node *p = head; p; p = p->next) printf("%d%s", p->data, p->next ? " " : "\n");
    }
    while (head) { Node *next = head->next; free(head); head = next; }
    return 0;
}
