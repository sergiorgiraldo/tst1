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
