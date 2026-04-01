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
