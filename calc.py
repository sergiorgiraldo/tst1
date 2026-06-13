import math
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


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

FUNCTIONS = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'abs': abs,
    'floor': math.floor,
    'ceil': math.ceil,
}

CONSTANTS = {
    'pi': math.pi,
    'e': math.e,
}


def evaluate(node, env: dict):
    if isinstance(node, Number):
        return node.value

    if isinstance(node, Variable):
        if node.name in env:
            return env[node.name]
        if node.name in CONSTANTS:
            return CONSTANTS[node.name]
        raise NameError(f"undefined variable '{node.name}'")

    if isinstance(node, UnaryOp):
        val = evaluate(node.operand, env)
        if node.op == '-':
            return -val
        raise ValueError(f"unknown unary operator '{node.op}'")

    if isinstance(node, BinOp):
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        if node.op == '+':
            return left + right
        if node.op == '-':
            return left - right
        if node.op == '*':
            return left * right
        if node.op == '/':
            return left / right
        if node.op == '//':
            return left // right
        if node.op == '%':
            return left % right
        if node.op == '**':
            return left ** right
        raise ValueError(f"unknown operator '{node.op}'")

    if isinstance(node, FunctionCall):
        if node.name not in FUNCTIONS:
            raise NameError(f"undefined function '{node.name}'")
        args = [evaluate(a, env) for a in node.args]
        return FUNCTIONS[node.name](*args)

    if isinstance(node, Assignment):
        value = evaluate(node.expr, env)
        env[node.name] = value
        return value

    raise TypeError(f"unknown AST node type '{type(node).__name__}'")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    env: dict = {}
    print("Simple calculator. Type 'quit' or 'exit' to leave.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text.lower() in ('quit', 'exit'):
            break

        try:
            ast = parse(text)
            result = evaluate(ast, env)
            print(result)
        except (LexError, ParseError) as e:
            pointer = ' ' * (e.pos + 2) + '^'
            print(text)
            print(pointer)
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
