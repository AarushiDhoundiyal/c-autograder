#include <stdio.h>
#include <stdlib.h>

struct node {
    int value;
    struct node *next;
};

/* Append a value after `tail`; returns the new node, or NULL if malloc fails. */
static struct node *append(struct node **head, struct node *tail, int value) {
    struct node *fresh = malloc(sizeof *fresh);
    if (fresh == NULL) {
        return NULL;
    }
    fresh->value = value;
    fresh->next = NULL;
    if (tail == NULL) {
        *head = fresh;
    } else {
        tail->next = fresh;
    }
    return fresh;
}

/* Reverse the list in place and return the new head. */
static struct node *reverse(struct node *head) {
    struct node *previous = NULL;
    while (head != NULL) {
        struct node *following = head->next;
        head->next = previous;
        previous = head;
        head = following;
    }
    return previous;
}

static void print_list(const struct node *head) {
    for (const struct node *p = head; p != NULL; p = p->next) {
        printf(p == head ? "%d" : " %d", p->value);
    }
    printf("\n");
}

static void free_list(struct node *head) {
    while (head != NULL) {
        struct node *following = head->next;
        free(head);
        head = following;
    }
}

int main(void) {
    int count;
    if (scanf("%d", &count) != 1 || count < 0) {
        return 1;
    }
    struct node *head = NULL, *tail = NULL;
    for (int i = 0; i < count; i++) {
        int value;
        if (scanf("%d", &value) != 1) {
            break;
        }
        tail = append(&head, tail, value);
        if (tail == NULL) {
            free_list(head);
            return 1;
        }
    }
    head = reverse(head);
    print_list(head);
    free_list(head);
    return 0;
}
