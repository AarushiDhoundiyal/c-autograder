#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int value;
    struct Node *next;
} Node;

/** Creates a new node holding `value`. */
static Node *create_node(int value) {
    Node *node = malloc(sizeof(Node));
    if (node == NULL) {
        fprintf(stderr, "Out of memory\n");
        exit(1);
    }
    node->value = value;
    node->next = NULL;
    return node;
}

/** Reverses the list recursively and returns the new head. */
static Node *reverse_list(Node *head) {
    if (head == NULL || head->next == NULL) {
        return head;
    }
    Node *new_head = reverse_list(head->next);
    head->next->next = head;
    head->next = NULL;
    return new_head;
}

static void print_list(const Node *head) {
    const Node *current = head;
    while (current != NULL) {
        printf(current == head ? "%d" : " %d", current->value);
        current = current->next;
    }
    printf("\n");
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
    Node dummy = {0, NULL};
    Node *tail = &dummy;
    for (int i = 0; i < n; i++) {
        int value;
        if (scanf("%d", &value) != 1) {
            break;
        }
        tail->next = create_node(value);
        tail = tail->next;
    }
    Node *head = reverse_list(dummy.next);
    print_list(head);
    free_list(head);
    return 0;
}
