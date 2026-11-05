# balanced_brackets

Read the whole input (at most 100000 characters). Only the six characters `( ) [ ] { }`
matter; every other character, including spaces and newlines, is ignored. Print `YES` if the
brackets are balanced and properly nested, otherwise print `NO`, followed by a newline.

Sample input: `{[()()]}`  Sample output: `YES`

Sample input: `([)]`  Sample output: `NO`

**Specification decisions.** Input with no brackets at all, including empty input, prints
`YES`. Nesting can be as deep as the input is long, so a stack of fixed small size is not
enough.
