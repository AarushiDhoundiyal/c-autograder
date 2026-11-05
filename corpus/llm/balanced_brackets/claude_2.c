#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>

typedef struct {
    char *items;
    int top;
    int capacity;
} Stack;

static void stack_init(Stack *s, int capacity) {
    s->items = malloc((size_t)capacity);
    s->top = 0;
    s->capacity = capacity;
}

static bool stack_push(Stack *s, char c) {
    if (s->top == s->capacity) {
        return false;
    }
    s->items[s->top++] = c;
    return true;
}

static bool stack_pop(Stack *s, char *out) {
    if (s->top == 0) {
        return false;
    }
    *out = s->items[--s->top];
    return true;
}

/** Returns true if `close` is the matching closing bracket for `open`. */
static bool matches(char open, char close) {
    return (open == '(' && close == ')') ||
           (open == '[' && close == ']') ||
           (open == '{' && close == '}');
}

/** Checks whether the brackets read from standard input are balanced. */
static bool is_balanced(void) {
    Stack s;
    stack_init(&s, 100000);
    bool ok = true;
    int c;
    while (ok && (c = getchar()) != EOF) {
        if (c == '(' || c == '[' || c == '{') {
            ok = stack_push(&s, (char)c);
        } else if (c == ')' || c == ']' || c == '}') {
            char open;
            ok = stack_pop(&s, &open) && matches(open, (char)c);
        }
    }
    ok = ok && s.top == 0;
    free(s.items);
    return ok;
}

int main(void) {
    printf("%s\n", is_balanced() ? "YES" : "NO");
    return 0;
}
