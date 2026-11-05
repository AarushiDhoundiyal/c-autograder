#include <stdio.h>
#include <stdlib.h>

struct node {
    int value;
    struct node *next;
};

/* Builds the reversed list by walking to the end of the old list for every node: O(n^2). */
struct node *reverse(struct node *head) {
    struct node *result = NULL, *rtail = NULL;
    while (head) {
        struct node *before = NULL, *last = head;
        while (last->next) {
            before = last;
            last = last->next;
        }
        if (before) {
            before->next = NULL;
        } else {
            head = NULL;
        }
        if (rtail) {
            rtail->next = last;
        } else {
            result = last;
        }
        rtail = last;
    }
    return result;
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
