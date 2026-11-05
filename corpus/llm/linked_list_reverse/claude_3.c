#include <stdio.h>
#include <stdlib.h>

typedef struct ListNode {
    int val;
    struct ListNode *next;
} ListNode;

/* Prints the list from the back using recursion */
static void print_reverse(const ListNode *node, int is_first) {
    if (node == NULL) {
        return;
    }
    print_reverse(node->next, 0);
    printf("%d%s", node->val, is_first ? "\n" : " ");
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1) {
        return 1;
    }
    ListNode dummy = {0, NULL};
    ListNode *tail = &dummy;
    for (int i = 0; i < n; i++) {
        ListNode *node = malloc(sizeof *node);
        if (!node || scanf("%d", &node->val) != 1) {
            return 1;
        }
        node->next = NULL;
        tail->next = node;
        tail = node;
    }
    if (dummy.next == NULL) {
        puts("EMPTY");
    } else {
        print_reverse(dummy.next, 1);
    }
    ListNode *p = dummy.next;
    while (p) {
        ListNode *next = p->next;
        free(p);
        p = next;
    }
    return 0;
}
