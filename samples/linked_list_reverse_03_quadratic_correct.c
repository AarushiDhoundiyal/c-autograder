#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int x; struct Node *next; } Node;
int main(void) {
    int n; if (scanf("%d", &n) != 1 || n < 0 || n > 100) return 1;
    Node *head = NULL, *tail = NULL;
    for (int i = 0; i < n; i++) {
        int x; if (scanf("%d", &x) != 1) return 1;
        Node *p = malloc(sizeof *p); if (!p) return 1;
        p->x = x; p->next = NULL;
        if (tail) tail->next = p; else head = p;
        tail = p;
    }
    if (n == 0) puts("EMPTY");
    for (int i = n - 1; i >= 0; --i) {
        Node *p = head;
        for (int j = 0; j < i; ++j) p = p->next;
        printf("%d%s", p->x, i ? " " : "\n");
    }
    while (head) { Node *next = head->next; free(head); head = next; }
    return 0;
}
