#include <stdio.h>

#define MOD 1000000007ULL

typedef struct {
    unsigned long long a, b, c, d;
} Matrix;

/* Multiply two 2x2 matrices modulo MOD */
static Matrix multiply(Matrix x, Matrix y) {
    Matrix r;
    r.a = (x.a * y.a + x.b * y.c) % MOD;
    r.b = (x.a * y.b + x.b * y.d) % MOD;
    r.c = (x.c * y.a + x.d * y.c) % MOD;
    r.d = (x.c * y.b + x.d * y.d) % MOD;
    return r;
}

/* Fast exponentiation of the Fibonacci matrix: O(log n) */
static unsigned long long ways(long long n) {
    Matrix result = {1, 0, 0, 1};
    Matrix base = {1, 1, 1, 0};
    long long power = n;
    while (power > 0) {
        if (power & 1) {
            result = multiply(result, base);
        }
        base = multiply(base, base);
        power >>= 1;
    }
    /* ways(n) = F(n + 1) = result.a when result = M^n */
    return result.a;
}

int main(void) {
    long long n;
    if (scanf("%lld", &n) != 1) {
        return 1;
    }
    printf("%llu\n", ways(n));
    return 0;
}
