# Sample outputs

The grader's output on all 68 sample submissions in `samples/`. For every sample there is a text report
(`<sample>.txt`, what a student reads) and a JSON report (`<sample>.json`, with the full evidence for
every metric). `SUMMARY.txt` lists all grades and flags.

Each JSON report records the versions of the tools used under `tool_versions`. A few grades can differ
slightly on another machine: for example, Ubuntu's gcc warns when the return value of `scanf` is ignored
and Debian's gcc does not, which changes the syntax metric of three samples by one point. Readability
uses the source features only unless an Ollama server is running.

To produce the reports again, run the samples in batches:

```bash
python scripts/run_samples.py --out-dir sample_outputs add sum_array
python scripts/run_samples.py --out-dir sample_outputs climb_stairs knapsack lis
python scripts/run_samples.py --out-dir sample_outputs hanoi nqueens permutations
python scripts/run_samples.py --out-dir sample_outputs reverse_list balanced_brackets
python scripts/run_samples.py --out-dir sample_outputs count_occurrences longest_run linked_list_reverse
python scripts/run_samples.py --out-dir sample_outputs graph_components stairs_dp
```

Each batch writes its own `SUMMARY_<problems>.txt`; `python scripts/run_samples.py --out-dir sample_outputs`
without problem names grades every sample and writes `SUMMARY.txt`.
