#include <stdio.h>
#include <stdlib.h>

typedef struct ListNode {
    int val;
    struct ListNode *next;
} ListNode;

/* Insert at the front while reading, then reverse once more to restore input order */
static ListNode *push_front(ListNode *head, int val) {
    ListNode *node = malloc(sizeof *node);
    node->val = val;
    node->next = head;
    return node;
}

static ListNode *reverse(ListNode *head) {
    ListNode *prev = NULL;
    while (head) {
        ListNode *nxt = head->next;
        head->next = prev;
        prev = head;
        head = nxt;
    }
    return prev;
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    ListNode *head = NULL;
    for (int i = 0; i < n; i++) {
        int x;
        scanf("%d", &x);
        head = push_front(head, x);
    }
    head = reverse(head);   /* list now in input order */
    head = reverse(head);   /* the required reversal */
    for (ListNode *p = head; p; p = p->next) {
        printf("%d%s", p->val, p->next ? " " : "");
    }
    printf("\n");
    while (head) {
        ListNode *nxt = head->next;
        free(head);
        head = nxt;
    }
    return 0;
}
