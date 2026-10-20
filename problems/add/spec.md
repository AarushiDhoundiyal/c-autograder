# Problem: add_two_integers

Read two integers on a single line, separated by whitespace, and print their
sum followed by a newline.

* Each input integer fits in a signed 32-bit `int`.
* **The sum can exceed 32 bits** and must be printed exactly (e.g. `2147483647 1` -> `2147483648`).
  Signed overflow is *undefined behaviour* in C, so the reference answer is the
  mathematically correct sum computed in `long long`.
* Input may contain extra spaces/tabs and may lack a trailing newline.

Sample input : `7 5`   Sample output: `12`
