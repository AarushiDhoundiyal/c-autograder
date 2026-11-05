#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int x; struct Node *next; } Node;
int main(void) {
    int n, x;
    if (scanf("%d", &n) != 1 || n < 0 || n > 100) return 1;
    Node *head = NULL, *tail = NULL;
    for (int i = 0; i < n; ++i) {
        if (scanf("%d", &x) != 1) return 1;
        Node *p = malloc(sizeof *p); if (!p) return 1;
        p->x = x; p->next = NULL;
        if (tail) tail->next = p; else head = p;
        tail = p;
    }
    Node *prev = NULL, *cur = head;
    while (cur) { Node *next = cur->next; cur->next = prev; prev = cur; cur = next; }
    if (!prev) puts("EMPTY");
    else for (Node *p = prev; p; p = p->next) printf("%d%s", p->x, p->next ? " " : "\n");
    while (prev) { Node *next = prev->next; free(prev); prev = next; }
    return 0;
}
