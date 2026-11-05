#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int val; struct Node *next; } Node;
int main(void) {
    int n; if (scanf("%d", &n) != 1 || n < 0 || n > 100) return 1;
    Node *head = NULL, *tail = NULL;
    for (int i = 0; i < n; ++i) {
        int x; if (scanf("%d", &x) != 1) return 1;
        Node *p = malloc(sizeof *p); if (!p) return 1;
        p->val = x; p->next = NULL;
        if (tail) tail->next = p; else head = p; tail = p;
    }
    if (!head) puts("EMPTY");
    else for (Node *p = head; p; p = p->next) printf("%d%s", p->val, p->next ? " " : "\n"); /* BUG */
    while (head) { Node *nxt = head->next; free(head); head = nxt; }
    return 0;
}
