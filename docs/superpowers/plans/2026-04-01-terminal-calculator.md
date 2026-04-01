# Terminal Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file Python terminal expression evaluator REPL with colorized output, in-session arrow-key history, variables, built-in math functions, and friendly inline error reporting.

**Architecture:** Four layers in one file — REPL (readline + ANSI colors), Lexer (tokenizer with char position tracking), Parser (recursive descent → AST), Evaluator (AST walker with session `env` dict). Smart int/float: integer arithmetic stays as Python `int` (arbitrary precision), non-exact results fall back to `float`.

**Tech Stack:** Python 3.x stdlib only (`math`, `readline`, `sys`). No third-party packages.

---

## File Structure

| File | Purpose |
|---|---|
| `calc.py` | Single source file — all four layers |
| `tests/test_calc.py` | All tests — import individual functions from `calc.py` |

---

### Task 1: Project scaffold and Lexer tokens

**Files:**
- Create: `calc.py`
- Create: `tests/test_calc.py`

- [ ] **Step 1: Create `calc.py` with Token dataclass and Lexer skeleton**

```python
# calc.py
import math
import readline
import sys
from dataclasses import dataclass
from typing import List, Optional, Any


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

@dataclass
class Token:
    type: str   # NUMBER, IDENT, PLUS, MINUS, STAR, SLASH, DSLASH, PERCENT,
                # DSTAR, LPAREN, RPAREN, COMMA, EQ, EOF
    value: Any  # raw string or numeric value
    pos: int    # character position in original input (0-indexed)


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class LexError(Exception):
    def __init__(self, message: str, pos: int):
        super().__init__(message)
        self.pos = pos


def tokenize(text: str) -> List[Token]:
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]

        if c.isspace():
            i += 1
            continue

        if c.isdigit() or (c == '.' and i + 1 < len(text) and text[i+1].isdigit()):
            start = i
            while i < len(text) and (text[i].isdigit() or text[i] == '.'):
                i += 1
            raw = text[start:i]
            value = int(raw) if '.' not in raw else float(raw)
            tokens.append(Token('NUMBER', value, start))
            continue

        if c.isalpha() or c == '_':
            start = i
            while i < len(text) and (text[i].isalnum() or text[i] == '_'):
                i += 1
            tokens.append(Token('IDENT', text[start:i], start))
            continue

        simple = {
            '+': 'PLUS', '-': 'MINUS', '*': 'STAR', '/': 'SLASH',
            '%': 'PERCENT', '(': 'LPAREN', ')': 'RPAREN', ',': 'COMMA',
        }

        if c == '*' and i + 1 < len(text) and text[i+1] == '*':
            tokens.append(Token('DSTAR', '**', i)); i += 2; continue
        if c == '/' and i + 1 < len(text) and text[i+1] == '/':
            tokens.append(Token('DSLASH', '//', i)); i += 2; continue
        if c == '=' and (i + 1 >= len(text) or text[i+1] != '='):
            tokens.append(Token('EQ', '=', i)); i += 1; continue

        if c in simple:
            tokens.append(Token(simple[c], c, i)); i += 1; continue

        raise LexError(f"unexpected character '{c}'", i)

    tokens.append(Token('EOF', None, len(text)))
    return tokens
```

- [ ] **Step 2: Create `tests/test_calc.py` with lexer tests**

```python
# tests/test_calc.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from calc import tokenize, Token, LexError
import pytest


def tok_types(text):
    return [t.type for t in tokenize(text)]

def tok_values(text):
    return [t.value for t in tokenize(text) if t.type != 'EOF']


class TestLexer:
    def test_simple_number(self):
        toks = tokenize('42')
        assert toks[0] == Token('NUMBER', 42, 0)

    def test_float_number(self):
        toks = tokenize('3.14')
        assert toks[0].type == 'NUMBER'
        assert abs(toks[0].value - 3.14) < 1e-9

    def test_operators(self):
        assert tok_types('+ - * / // % **') == [
            'PLUS','MINUS','STAR','SLASH','DSLASH','PERCENT','DSTAR','EOF']

    def test_ident(self):
        toks = tokenize('foo_bar')
        assert toks[0] == Token('IDENT', 'foo_bar', 0)

    def test_position_tracking(self):
        toks = tokenize('1 + 2')
        assert toks[0].pos == 0
        assert toks[1].pos == 2
        assert toks[2].pos == 4

    def test_lex_error(self):
        with pytest.raises(LexError) as exc:
            tokenize('1 @ 2')
        assert exc.value.pos == 2

    def test_eq_token(self):
        assert tok_types('x = 5') == ['IDENT', 'EQ', 'NUMBER', 'EOF']
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd /Users/avenuecreek/source/tst1
python -m pytest tests/test_calc.py::TestLexer -v
```

Expected: all 7 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add calc.py tests/test_calc.py
git commit -m "feat: add Lexer with position-tracking tokenizer"
```

---

### Task 2: AST nodes and Parser

**Files:**
- Modify: `calc.py` — add AST dataclasses and Parser class
- Modify: `tests/test_calc.py` — add parser tests

- [ ] **Step 1: Add AST node dataclasses to `calc.py`** (after the Lexer section)

```python
# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------

@dataclass
class Number:
    value: Any          # int or float
    pos: int

@dataclass
class BinOp:
    op: str             # '+', '-', '*', '/', '//', '%', '**'
    left: Any
    right: Any
    pos: int

@dataclass
class UnaryOp:
    op: str             # '-'
    operand: Any
    pos: int

@dataclass
class Variable:
    name: str
    pos: int

@dataclass
class FunctionCall:
    name: str
    args: list
    pos: int

@dataclass
class Assignment:
    name: str
    expr: Any
    pos: int
```

- [ ] **Step 2: Add Parser class to `calc.py`** (after the AST nodes section)

```python
# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class ParseError(Exception):
    def __init__(self, message: str, pos: int):
        super().__init__(message)
        self.pos = pos


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def consume(self, expected_type: Optional[str] = None) -> Token:
        tok = self.tokens[self.pos]
        if expected_type and tok.type != expected_type:
            raise ParseError(
                f"expected '{expected_type}' but got '{tok.value}'", tok.pos)
        self.pos += 1
        return tok

    def parse(self):
        node = self.parse_assignment()
        if self.peek().type != 'EOF':
            tok = self.peek()
            raise ParseError(f"unexpected token '{tok.value}'", tok.pos)
        return node

    def parse_assignment(self):
        # assignment: IDENT EQ expr  |  expr
        if (self.peek().type == 'IDENT'
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == 'EQ'):
            name_tok = self.consume('IDENT')
            self.consume('EQ')
            expr = self.parse_expr()
            return Assignment(name_tok.value, expr, name_tok.pos)
        return self.parse_expr()

    def parse_expr(self):
        return self.parse_additive()

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().type in ('PLUS', 'MINUS'):
            op_tok = self.consume()
            op = op_tok.value
            right = self.parse_multiplicative()
            left = BinOp(op, left, right, op_tok.pos)
        return left

    def parse_multiplicative(self):
        left = self.parse_power()
        while self.peek().type in ('STAR', 'SLASH', 'DSLASH', 'PERCENT'):
            op_tok = self.consume()
            right = self.parse_power()
            left = BinOp(op_tok.value, left, right, op_tok.pos)
        return left

    def parse_power(self):
        base = self.parse_unary()
        if self.peek().type == 'DSTAR':
            op_tok = self.consume()
            exp = self.parse_power()  # right-associative
            return BinOp('**', base, exp, op_tok.pos)
        return base

    def parse_unary(self):
        if self.peek().type == 'MINUS':
            op_tok = self.consume()
            return UnaryOp('-', self.parse_unary(), op_tok.pos)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()

        if tok.type == 'NUMBER':
            self.consume()
            return Number(tok.value, tok.pos)

        if tok.type == 'IDENT':
            self.consume()
            if self.peek().type == 'LPAREN':
                # function call
                self.consume('LPAREN')
                args = []
                if self.peek().type != 'RPAREN':
                    args.append(self.parse_expr())
                    while self.peek().type == 'COMMA':
                        self.consume('COMMA')
                        args.append(self.parse_expr())
                self.consume('RPAREN')
                return FunctionCall(tok.value, args, tok.pos)
            return Variable(tok.value, tok.pos)

        if tok.type == 'LPAREN':
            self.consume('LPAREN')
            node = self.parse_expr()
            self.consume('RPAREN')
            return node

        raise ParseError(f"unexpected token '{tok.value}'", tok.pos)


def parse(text: str):
    tokens = tokenize(text)
    return Parser(tokens).parse()
```

- [ ] **Step 3: Add parser tests to `tests/test_calc.py`**

```python
from calc import (tokenize, Token, LexError,
                  Number, BinOp, UnaryOp, Variable, FunctionCall, Assignment,
                  ParseError, parse)


class TestParser:
    def test_number(self):
        assert isinstance(parse('42'), Number)

    def test_binop_add(self):
        node = parse('1 + 2')
        assert isinstance(node, BinOp)
        assert node.op == '+'

    def test_precedence_mul_over_add(self):
        node = parse('1 + 2 * 3')
        # top node should be +, right child is *
        assert node.op == '+'
        assert isinstance(node.right, BinOp)
        assert node.right.op == '*'

    def test_power_right_assoc(self):
        node = parse('2 ** 3 ** 2')
        # 2 ** (3 ** 2), top is **, right is **
        assert node.op == '**'
        assert isinstance(node.right, BinOp)

    def test_unary_minus(self):
        node = parse('-5')
        assert isinstance(node, UnaryOp)
        assert node.op == '-'

    def test_variable(self):
        node = parse('x')
        assert isinstance(node, Variable)
        assert node.name == 'x'

    def test_function_call(self):
        node = parse('sqrt(16)')
        assert isinstance(node, FunctionCall)
        assert node.name == 'sqrt'
        assert len(node.args) == 1

    def test_assignment(self):
        node = parse('x = 5 + 3')
        assert isinstance(node, Assignment)
        assert node.name == 'x'

    def test_parse_error_unexpected_token(self):
        with pytest.raises(ParseError) as exc:
            parse('2 + * 3')
        assert exc.value.pos == 4  # position of '*'

    def test_parse_error_trailing_token(self):
        with pytest.raises(ParseError):
            parse('1 2')
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_calc.py::TestParser -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add calc.py tests/test_calc.py
git commit -m "feat: add AST nodes and recursive descent Parser"
```

---

### Task 3: Evaluator with smart int/float

**Files:**
- Modify: `calc.py` — add Evaluator class
- Modify: `tests/test_calc.py` — add evaluator tests

- [ ] **Step 1: Add Evaluator to `calc.py`** (after the Parser section)

```python
# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class EvalError(Exception):
    pass


# Math functions exposed to the calculator (all public math.* callables)
_MATH_FUNCTIONS = {
    name: getattr(math, name)
    for name in dir(math)
    if callable(getattr(math, name)) and not name.startswith('_')
}


def _make_env() -> dict:
    """Return a fresh session environment pre-loaded with constants."""
    return {'pi': math.pi, 'e': math.e}


def _is_int_result(op: str, left, right) -> bool:
    """True when both operands are int and the operation keeps the result exact."""
    if not (isinstance(left, int) and isinstance(right, int)):
        return False
    return op in ('+', '-', '*')


def evaluate(node, env: dict):
    if isinstance(node, Number):
        return node.value

    if isinstance(node, UnaryOp):
        val = evaluate(node.operand, env)
        return -val

    if isinstance(node, BinOp):
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        op = node.op
        if op == '+':
            return left + right
        if op == '-':
            return left - right
        if op == '*':
            return left * right
        if op == '/':
            if right == 0:
                raise EvalError('division by zero')
            return left / right
        if op == '//':
            if right == 0:
                raise EvalError('division by zero')
            return left // right
        if op == '%':
            if right == 0:
                raise EvalError('division by zero')
            return left % right
        if op == '**':
            # keep int when base and exponent are both non-negative ints
            if isinstance(left, int) and isinstance(right, int) and right >= 0:
                return left ** right
            return float(left) ** float(right)
        raise EvalError(f"unknown operator '{op}'")

    if isinstance(node, Variable):
        if node.name not in env:
            raise EvalError(f"undefined variable '{node.name}'")
        return env[node.name]

    if isinstance(node, FunctionCall):
        if node.name not in _MATH_FUNCTIONS:
            raise EvalError(f"unknown function '{node.name}'")
        args = [evaluate(a, env) for a in node.args]
        try:
            return _MATH_FUNCTIONS[node.name](*args)
        except (TypeError, ValueError) as exc:
            raise EvalError(str(exc)) from exc

    if isinstance(node, Assignment):
        value = evaluate(node.expr, env)
        env[node.name] = value
        return value

    raise EvalError(f"unknown node type '{type(node).__name__}'")
```

- [ ] **Step 2: Add evaluator tests to `tests/test_calc.py`**

```python
from calc import (tokenize, Token, LexError,
                  Number, BinOp, UnaryOp, Variable, FunctionCall, Assignment,
                  ParseError, parse,
                  EvalError, evaluate, _make_env)


class TestEvaluator:
    def setup_method(self):
        self.env = _make_env()

    def eval(self, text):
        return evaluate(parse(text), self.env)

    def test_integer_addition(self):
        assert self.eval('2 + 3') == 5
        assert isinstance(self.eval('2 + 3'), int)

    def test_float_division(self):
        result = self.eval('10 / 4')
        assert abs(result - 2.5) < 1e-9
        assert isinstance(result, float)

    def test_floor_division(self):
        assert self.eval('10 // 3') == 3

    def test_modulo(self):
        assert self.eval('10 % 3') == 1

    def test_precedence(self):
        assert self.eval('2 + 3 * 4') == 14

    def test_parentheses(self):
        assert self.eval('(2 + 3) * 4') == 20

    def test_unary_minus(self):
        assert self.eval('-5') == -5

    def test_exponentiation(self):
        result = self.eval('2 ** 10')
        assert result == 1024
        assert isinstance(result, int)

    def test_big_integer(self):
        result = self.eval('factorial(100)')
        assert isinstance(result, int)
        assert result > 10**157

    def test_pi_constant(self):
        assert abs(self.eval('pi') - math.pi) < 1e-12

    def test_e_constant(self):
        assert abs(self.eval('e') - math.e) < 1e-12

    def test_sqrt(self):
        assert abs(self.eval('sqrt(16)') - 4.0) < 1e-9

    def test_variable_assignment(self):
        self.eval('x = 10')
        assert self.env['x'] == 10

    def test_variable_use(self):
        self.eval('x = 7')
        assert self.eval('x * 2') == 14

    def test_division_by_zero(self):
        with pytest.raises(EvalError, match='division by zero'):
            self.eval('1 / 0')

    def test_undefined_variable(self):
        with pytest.raises(EvalError, match="undefined variable 'foo'"):
            self.eval('foo')
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/test_calc.py::TestEvaluator -v
```

Expected: all 16 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add calc.py tests/test_calc.py
git commit -m "feat: add Evaluator with smart int/float and math built-ins"
```

---

### Task 4: REPL with colors and readline

**Files:**
- Modify: `calc.py` — add color helpers and `main()` REPL function

- [ ] **Step 1: Add ANSI color helpers and `main()` to `calc.py`** (at the bottom, after the Evaluator)

```python
# ---------------------------------------------------------------------------
# Colors (ANSI — no third-party library)
# ---------------------------------------------------------------------------

_CYAN  = '\033[36m'
_GREEN = '\033[32m'
_RED   = '\033[31m'
_RESET = '\033[0m'

def _cyan(s):  return f'{_CYAN}{s}{_RESET}'
def _green(s): return f'{_GREEN}{s}{_RESET}'
def _red(s):   return f'{_RED}{s}{_RESET}'


def _format_result(value) -> str:
    if isinstance(value, int):
        return str(value)
    # float: up to 10 significant digits, strip trailing zeros
    formatted = f'{value:.10g}'
    return formatted


def _caret_line(text: str, pos: int) -> str:
    """Return two lines: the original input indented, then a caret at pos."""
    return f'  {text}\n  {" " * pos}^'


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

def main():
    import readline as _rl  # noqa: F401 — imported for side-effect (line editing)

    env = _make_env()
    print("calc — type an expression, 'quit' to exit")

    while True:
        try:
            line = input(_cyan('> '))
        except (EOFError, KeyboardInterrupt):
            print()
            break

        line = line.strip()
        if not line:
            continue
        if line in ('quit', 'exit'):
            break

        try:
            tokens = tokenize(line)
            ast = Parser(tokens).parse()
            result = evaluate(ast, env)
            print(_green(_format_result(result)))
        except LexError as exc:
            print(_red(f'Error: {exc}'))
            print(_red(_caret_line(line, exc.pos)))
        except ParseError as exc:
            print(_red(f'Error: {exc}'))
            print(_red(_caret_line(line, exc.pos)))
        except EvalError as exc:
            print(_red(f'Error: {exc}'))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Smoke-test the REPL manually**

```bash
python3 calc.py
```

Try:
```
> 2 + 3 * (4 - 1)        # expect: 11
> x = 100 / 4             # expect: 25.0
> x * pi                  # expect: ~78.5398...
> factorial(20)            # expect: 2432902008176640000
> 2 + * 3                  # expect: red error with caret
> foo                      # expect: red "undefined variable 'foo'"
> quit
```

- [ ] **Step 3: Run full test suite**

```bash
python -m pytest tests/test_calc.py -v
```

Expected: all 33 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add calc.py
git commit -m "feat: add REPL with readline history, ANSI colors, and error caret"
```

---

### Task 5: REPL color and format unit tests

**Files:**
- Modify: `tests/test_calc.py` — add tests for `_format_result` and `_caret_line`

- [ ] **Step 1: Add formatting tests to `tests/test_calc.py`**

```python
from calc import (tokenize, Token, LexError,
                  Number, BinOp, UnaryOp, Variable, FunctionCall, Assignment,
                  ParseError, parse,
                  EvalError, evaluate, _make_env,
                  _format_result, _caret_line)
import math


class TestFormatResult:
    def test_integer_no_decimal(self):
        assert _format_result(42) == '42'

    def test_large_integer(self):
        assert _format_result(10**20) == str(10**20)

    def test_float_truncates_trailing_zeros(self):
        assert _format_result(2.5) == '2.5'

    def test_float_pi(self):
        result = _format_result(math.pi)
        assert result.startswith('3.141592')

    def test_zero_float(self):
        assert _format_result(0.0) == '0'


class TestCaretLine:
    def test_caret_at_position(self):
        line = '2 + * 3'
        output = _caret_line(line, 4)
        lines = output.split('\n')
        assert '2 + * 3' in lines[0]
        assert lines[1].index('^') == lines[1].index('^')
        # caret should be at offset 4 + 2 (indent)
        assert lines[1] == '  ' + ' ' * 4 + '^'
```

- [ ] **Step 2: Run tests**

```bash
python -m pytest tests/test_calc.py::TestFormatResult tests/test_calc.py::TestCaretLine -v
```

Expected: all 8 tests PASS.

- [ ] **Step 3: Run full suite**

```bash
python -m pytest tests/test_calc.py -v
```

Expected: all 41 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_calc.py
git commit -m "test: add format_result and caret_line unit tests"
```

---

## Spec Coverage Checklist

| Spec requirement | Covered by |
|---|---|
| Expression evaluator REPL | Task 4 — `main()` |
| Arrow-key history in-session | Task 4 — `import readline` |
| Variables (`x = expr`) | Task 3 — `Assignment` node |
| Built-in constants `pi`, `e` | Task 3 — `_make_env()` |
| All `math.*` functions | Task 3 — `_MATH_FUNCTIONS` |
| Operator precedence | Task 2 — Parser, Task 3 tests |
| Smart int/float | Task 3 — `evaluate()` |
| Big integers exact | Task 3 — `test_big_integer` |
| Parse error + caret | Task 4 — REPL catch block, Task 5 |
| Eval error (div/0, undef var) | Task 3 tests, Task 4 REPL |
| Cyan prompt, green result, red error | Task 4 — color helpers |
| Single file, no deps | All tasks — stdlib only |
