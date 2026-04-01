import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from calc import (tokenize, Token, LexError,
                  Number, BinOp, UnaryOp, Variable, FunctionCall, Assignment,
                  ParseError, parse)
import pytest


def tok_types(text):
    return [t.type for t in tokenize(text)]


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
