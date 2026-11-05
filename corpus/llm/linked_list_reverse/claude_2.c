#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int value;
    struct Node *next;
} Node;

/** Appends a node with the given value after tail and returns the new tail. */
static Node *append(Node **head, Node *tail, int value) {
    Node *node = malloc(sizeof(Node));
    if (node == NULL) {
        return NULL;
    }
    node->value = value;
    node->next = NULL;
    if (tail == NULL) {
        *head = node;
    } else {
        tail->next = node;
    }
    return node;
}

/** Reverses the list in place and returns the new head. */
static Node *reverse(Node *head) {
    Node *prev = NULL;
    while (head != NULL) {
        Node *next = head->next;
        head->next = prev;
        prev = head;
        head = next;
    }
    return prev;
}

static void print_list(const Node *head) {
    if (head == NULL) {
        printf("EMPTY\n");
        return;
    }
    for (const Node *p = head; p != NULL; p = p->next) {
        printf(p->next ? "%d " : "%d\n", p->value);
    }
}

static void free_list(Node *head) {
    while (head != NULL) {
        Node *next = head->next;
        free(head);
        head = next;
    }
}

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n < 0) {
        return 1;
    }
    Node *head = NULL, *tail = NULL;
    for (int i = 0; i < n; i++) {
        int value;
        if (scanf("%d", &value) != 1 || (tail = append(&head, tail, value)) == NULL) {
            free_list(head);
            return 1;
        }
    }
    head = reverse(head);
    print_list(head);
    free_list(head);
    return 0;
}
