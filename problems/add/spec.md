# add_two_integers

Read two integers on a single line separated by whitespace and print their sum followed by a newline.

Sample input: `7 5`  Sample output: `12`

**Specification decision.** Both inputs fit in a 32-bit signed int, but the sum may not. The expected
answer is the **exact mathematical sum** (computed in `long long`), e.g. `2147483647 1` -> `2147483648`.
Signed overflow is undefined behaviour in C, so a wrapped value such as `-2147483648` is not a
guaranteed result and is not accepted.
