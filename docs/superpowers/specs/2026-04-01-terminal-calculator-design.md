# Terminal macOS Calculator — Design Spec

**Date:** 2026-04-01
**Status:** Approved

## Overview

A terminal expression evaluator REPL for macOS, written in Python (stdlib only). The user types mathematical expressions at a prompt, sees colorized results, and can use variables and built-in math functions. No installation or dependencies beyond Python 3.x.

## Architecture

The calculator is a single file (`calc.py`) with four separated layers:

1. **REPL** — entry point. Owns the `readline`-based input loop, prints the colored prompt `> `, dispatches each line to the evaluator. Handles `quit`/`exit` and `KeyboardInterrupt` gracefully.
2. **Lexer** — tokenizes the raw input string into a flat list of tokens (numbers, operators, identifiers, parentheses). Tracks each token's character position for error reporting.
3. **Parser** — recursive descent parser that consumes the token list and builds an AST. Raises `ParseError(message, position)` on invalid input.
4. **Evaluator** — walks the AST, resolves variable references from a session-scoped `env` dict, and returns a numeric result. Handles assignment (`x = expr`) by evaluating the RHS and storing in `env`.

A top-level `env` dict is initialized at startup with `pi = math.pi` and `e = math.e`, and persists for the lifetime of the session.

## Supported Syntax

```
2 + 3 * (4 - 1)       # arithmetic with precedence
x = 10 / 2             # variable assignment
x * pi                 # variable + constant
sqrt(16) + e           # built-in math functions
factorial(20)          # large integer results
```

Supported operators: `+`, `-`, `*`, `/`, `//` (floor div), `%` (modulo), `**` (exponentiation), unary `-`.

## AST Node Types

- `Number` — literal numeric value
- `BinOp` — binary operation with left, operator, right
- `UnaryOp` — unary minus
- `Variable` — named reference resolved from `env`
- `FunctionCall` — call to a `math.*` function
- `Assignment` — `name = expr`, stores result in `env`

## Number Handling

Smart int/float strategy:

- When all operands are integers and the operation is exact (add, subtract, multiply, integer exponent), Python's arbitrary-precision `int` is used — no size limit, no floating point error.
- Operations that produce non-integer results (division, `sqrt`, trig, etc.) use IEEE 754 `float`.
- Display: integers show without decimal point (`5`), floats show with up to 10 significant digits (`2.5`, `3.1415926536`).

This means `factorial(100)` is exact, and `0.1 + 0.2` returns `0.30000000000000004` (standard float behavior, documented behavior).

## Error Handling

Errors are caught at two points:

**Parse errors** (bad syntax): show message, line, and a caret at the token position:
```
Error: unexpected token '*'
  2 + * 3
      ^
```

**Eval errors** (division by zero, undefined variable): show message without caret:
```
Error: undefined variable 'foo'
Error: division by zero
```

In both cases the REPL continues running after printing the error.

## Display & Colors

ANSI escape codes only — no third-party library. Works in macOS Terminal and iTerm2.

| Element | Color |
|---|---|
| Prompt `> ` | Cyan |
| Result | Green |
| Error message | Red |

## In-Session History

`import readline` is sufficient. Arrow keys (↑/↓), Ctrl-A/Ctrl-E, backspace, and Ctrl-C all work within the session. No history is saved to disk between sessions.

## Built-in Functions & Constants

All functions from Python's `math` module are available: `sqrt`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `log`, `log2`, `log10`, `exp`, `floor`, `ceil`, `factorial`, `gcd`, etc.

Built-in constants: `pi`, `e`.

## File Layout

```
calc.py        # single file, ~250 lines
```

No `requirements.txt`. Runs with: `python3 calc.py`

## Out of Scope

- Persistent history across sessions
- Complex numbers
- Matrix / symbolic math
- Unit conversions
- Graphing or plotting
