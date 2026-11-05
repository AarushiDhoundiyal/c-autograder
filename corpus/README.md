# Originality corpus

`similarity_flag` compares every submission with the `.c` files in this folder that belong to
its problem. The folder name of a problem is the `"problem"` value of its rules file
(for example `add_two_integers`, `sum_array`, `knapsack`).

    corpus/llm/<problem>/      solutions written by language models
    corpus/online/<problem>/   solutions collected from websites
    corpus/peers/<problem>/    submissions of earlier batches (python manage.py export_corpus <problem>)

A match above the threshold raises a flag of kind `llm_copy`, `online_copy` or `similarity`
(for peers). Loose `.c` files placed directly in `corpus/` or `corpus/<kind>/` are compared
with every problem.

Current classmates are not stored here. The web application compares each submission with the
latest submission of every other student for the same problem while grading, and on the
command line the same is done with `python grade.py <file> --rules <rules> --peers <folder>`.

## What is included

* `llm/<problem>/claude_1.c` to `claude_3.c`: three solutions per problem written by Claude
  (Anthropic), in the styles a language model usually produces: a commented straightforward
  version, a version split into documented helper functions, and an alternative algorithm.
  Each one passes all hidden tests of its problem.
* `online/add_two_integers/online_example_1.c`: one example of a collected online solution.

## Adding more

* LLM answers from a local model: `python scripts/make_llm_corpus.py [problem ...] --count 3`
  (needs Ollama; answers that do not compile are skipped).
* Answers from other assistants (ChatGPT, Gemini, Copilot): give them the problem's `spec.md`
  and save each answer as a new `.c` file in `llm/<problem>/`.
* Online solutions: copy common solutions from sites such as GeeksforGeeks, Programiz or GitHub
  into `online/<problem>/`, one file per solution.

The check can only flag copies of solutions that are in this folder; a source that is not
collected here is never matched.
