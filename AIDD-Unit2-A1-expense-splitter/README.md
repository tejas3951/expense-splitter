# Expense Splitter — AIDD Unit 2, Assignment A1

A small command-line-friendly module that splits shared expenses, computes each
person's net balance, and produces the minimum-style list of transfers needed to
settle up. Money is handled as integer cents, so no rounding drift accumulates.

**AI tool used:** <!-- TODO: name the tool you actually used, e.g. Cursor (Composer / Agent) -->

## Features

- `split_equally(amount, people)`: equal split where leftover cents go to the first people in order (100.00 among 3 → 33.34 / 33.33 / 33.33).
- `Expense`: validated record of who paid, how much, and who shared it.
- `compute_balances(expenses)`: net position per person; always sums to zero.
- `settle(balances)`: greedy list of transfers that clears every balance.

## Setup and run

Requires Python 3.10+. No third-party dependencies.

```bash
# run the demo
python src/expense_splitter.py

# run the tests
python -m unittest discover -s tests -v
```

## Prompting techniques used (Class 04)

<!-- TODO: after you finish your own work, replace each line with what you actually did. -->

- **Zero-shot:** <where you used it, e.g. "scaffolding `split_equally` from a plain-language spec">
- **Few-shot:** <where you used it, e.g. "matching the docstring and test naming style from two examples">
- **Chain-of-thought:** <where you used it, e.g. "tracing the 100 ÷ 3 rounding bug and the leftover cent">

See `docs/PROMPT_LOG.md` for the full log.

## Project layout

```
src/expense_splitter.py        core logic and demo
tests/test_expense_splitter.py unit tests (unittest, stdlib only)
docs/PROMPT_LOG.md             prompt log and reflection
docs/screenshots/              screenshots of tool responses
```
