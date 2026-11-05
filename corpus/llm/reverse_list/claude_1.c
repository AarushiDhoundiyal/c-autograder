#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node* next;
};

int main() {
    int n;
    scanf("%d", &n);

    struct Node* head = NULL;
    struct Node* tail = NULL;

    // Build the linked list in input order
    for (int i = 0; i < n; i++) {
        struct Node* newNode = (struct Node*)malloc(sizeof(struct Node));
        scanf("%d", &newNode->data);
        newNode->next = NULL;
        if (head == NULL) {
            head = newNode;
            tail = newNode;
        } else {
            tail->next = newNode;
            tail = newNode;
        }
    }

    // Reverse the list in place
    struct Node* prev = NULL;
    struct Node* current = head;
    while (current != NULL) {
        struct Node* next = current->next;
        current->next = prev;
        prev = current;
        current = next;
    }
    head = prev;

    // Print the reversed list
    struct Node* temp = head;
    while (temp != NULL) {
        printf("%d", temp->data);
        if (temp->next != NULL) printf(" ");
        temp = temp->next;
    }
    printf("\n");

    // Free memory
    while (head != NULL) {
        struct Node* next = head->next;
        free(head);
        head = next;
    }
    return 0;
}
