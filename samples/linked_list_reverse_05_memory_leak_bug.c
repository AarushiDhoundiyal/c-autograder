#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int x; struct Node *next; } Node;
int main(void) {
    int n; if (scanf("%d", &n) != 1 || n < 0 || n > 100) return 1;
    Node *head = NULL;
    for (int i = 0; i < n; ++i) {
        int x; if (scanf("%d", &x) != 1) return 1;
        Node *p = malloc(sizeof *p); if (!p) return 1;
        p->x = x; p->next = head; head = p;
    }
    if (!head) puts("EMPTY");
    else for (Node *p = head; p; p = p->next) printf("%d%s", p->x, p->next ? " " : "\n");
    /* BUG: allocated nodes are never freed */
    return 0;
}
