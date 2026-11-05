#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node* next;
};

int main() {
    int n;
    scanf("%d", &n);

    if (n == 0) {
        printf("EMPTY\n");
        return 0;
    }

    struct Node* head = NULL;
    struct Node* tail = NULL;

    // Create the linked list in input order
    for (int i = 0; i < n; i++) {
        struct Node* newNode = (struct Node*)malloc(sizeof(struct Node));
        scanf("%d", &newNode->data);
        newNode->next = NULL;
        if (head == NULL) {
            head = tail = newNode;
        } else {
            tail->next = newNode;
            tail = newNode;
        }
    }

    // Reverse the list
    struct Node* prev = NULL;
    struct Node* curr = head;
    while (curr != NULL) {
        struct Node* next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
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

    // Free the list
    while (head != NULL) {
        struct Node* next = head->next;
        free(head);
        head = next;
    }
    return 0;
}
