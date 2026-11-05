#include <stdio.h>

#define MAX_CAPACITY 10000

static long long best[MAX_CAPACITY + 1];

/* Add one item to the table. Capacities go downwards so the item is used at most once. */
static void add_item(int capacity, int weight, long long value) {
    for (int c = capacity; c >= weight; c--) {
        long long with_item = best[c - weight] + value;
        if (with_item > best[c]) {
            best[c] = with_item;
        }
    }
}

int main(void) {
    int items, capacity;
    if (scanf("%d %d", &items, &capacity) != 2 || capacity < 0 || capacity > MAX_CAPACITY) {
        return 1;
    }
    for (int i = 0; i < items; i++) {
        int weight;
        long long value;
        if (scanf("%d %lld", &weight, &value) != 2) {
            return 1;
        }
        add_item(capacity, weight, value);
    }
    printf("%lld\n", best[capacity]);
    return 0;
}
