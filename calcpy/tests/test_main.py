import pytest

import math

from main import (
    Token,
    LexError,
    tokenize,
    Number,
    BinOp,
    UnaryOp,
    Variable,
    FunctionCall,
    Assignment,
    Parser,
    ParseError,
    parse,
    evaluate,
    FUNCTIONS,
    CONSTANTS,
)


def calc(text, env=None):
    return evaluate(parse(text), {} if env is None else env)


def types(text):
    return [t.type for t in tokenize(text)]


def test_empty_string_gives_eof():
    toks = tokenize("")
    assert len(toks) == 1
    assert toks[0].type == "EOF"
    assert toks[0].value is None
    assert toks[0].pos == 0


def test_integer_number():
    toks = tokenize("42")
    assert toks[0].type == "NUMBER"
    assert toks[0].value == 42
    assert isinstance(toks[0].value, int)
    assert toks[0].pos == 0
    assert toks[1].type == "EOF"


def test_float_number():
    toks = tokenize("3.14")
    assert toks[0].type == "NUMBER"
    assert toks[0].value == 3.14
    assert isinstance(toks[0].value, float)


def test_leading_dot_float():
    toks = tokenize(".5")
    assert toks[0].type == "NUMBER"
    assert toks[0].value == 0.5
    assert isinstance(toks[0].value, float)


def test_identifier():
    toks = tokenize("foo")
    assert toks[0].type == "IDENT"
    assert toks[0].value == "foo"


def test_identifier_with_underscore_and_digits():
    toks = tokenize("_x1")
    assert toks[0].type == "IDENT"
    assert toks[0].value == "_x1"


def test_simple_operators():
    assert types("+ - * / % ( ) ,") == [
        "PLUS", "MINUS", "STAR", "SLASH", "PERCENT",
        "LPAREN", "RPAREN", "COMMA", "EOF",
    ]


def test_double_star():
    toks = tokenize("**")
    assert toks[0].type == "DSTAR"
    assert toks[0].value == "**"
    assert toks[1].type == "EOF"


def test_double_slash():
    toks = tokenize("//")
    assert toks[0].type == "DSLASH"
    assert toks[0].value == "//"


def test_single_star_vs_double_star():
    assert types("*") == ["STAR", "EOF"]
    assert types("***") == ["DSTAR", "STAR", "EOF"]


def test_equals():
    toks = tokenize("=")
    assert toks[0].type == "EQ"
    assert toks[0].value == "="


def test_whitespace_ignored():
    assert types("  1   +   2  ") == ["NUMBER", "PLUS", "NUMBER", "EOF"]


def test_positions_tracked():
    toks = tokenize("1 + 20")
    assert toks[0].pos == 0
    assert toks[1].pos == 2
    assert toks[2].pos == 4
    assert toks[2].value == 20


def test_expression_types():
    assert types("x = 2 ** 3 + foo(1, 2)") == [
        "IDENT", "EQ", "NUMBER", "DSTAR", "NUMBER", "PLUS",
        "IDENT", "LPAREN", "NUMBER", "COMMA", "NUMBER", "RPAREN", "EOF",
    ]


def test_eof_position_is_end():
    text = "1+2"
    toks = tokenize(text)
    assert toks[-1].type == "EOF"
    assert toks[-1].pos == len(text)


def test_unexpected_character_raises():
    with pytest.raises(LexError) as exc:
        tokenize("1 @ 2")
    assert exc.value.pos == 2


def test_double_equals_raises():
    with pytest.raises(LexError):
        tokenize("==")


def test_lexerror_carries_message_and_pos():
    err = LexError("bad", 5)
    assert err.pos == 5
    assert str(err) == "bad"


def test_token_dataclass_fields():
    t = Token("NUMBER", 7, 3)
    assert t.type == "NUMBER"
    assert t.value == 7
    assert t.pos == 3


def test_only_whitespace_gives_eof():
    toks = tokenize("   \t\n ")
    assert len(toks) == 1
    assert toks[0].type == "EOF"


def test_multi_digit_int_value():
    toks = tokenize("1000")
    assert toks[0].value == 1000
    assert isinstance(toks[0].value, int)


def test_trailing_dot_float():
    toks = tokenize("5.")
    assert toks[0].type == "NUMBER"
    assert toks[0].value == 5.0
    assert isinstance(toks[0].value, float)


def test_adjacent_number_and_ident():
    assert [t.type for t in tokenize("2x")] == ["NUMBER", "IDENT", "EOF"]


def test_double_slash_then_slash():
    assert [t.type for t in tokenize("///")] == ["DSLASH", "SLASH", "EOF"]


def test_ident_value_and_pos():
    toks = tokenize("  abc")
    assert toks[0].value == "abc"
    assert toks[0].pos == 2


def test_unexpected_char_at_start():
    with pytest.raises(LexError) as exc:
        tokenize("@")
    assert exc.value.pos == 0


def test_number_dataclass():
    n = Number(3, 0)
    assert n.value == 3
    assert n.pos == 0


def test_binop_dataclass():
    node = BinOp("+", Number(1, 0), Number(2, 2), 1)
    assert node.op == "+"
    assert node.left.value == 1
    assert node.right.value == 2
    assert node.pos == 1


def test_unaryop_dataclass():
    node = UnaryOp("-", Number(5, 1), 0)
    assert node.op == "-"
    assert node.operand.value == 5


def test_variable_dataclass():
    v = Variable("x", 4)
    assert v.name == "x"
    assert v.pos == 4


def test_functioncall_dataclass():
    call = FunctionCall("max", [Number(1, 0), Number(2, 0)], 0)
    assert call.name == "max"
    assert len(call.args) == 2


def test_assignment_dataclass():
    a = Assignment("y", Number(9, 4), 0)
    assert a.name == "y"
    assert a.expr.value == 9


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def test_parse_number():
    node = parse("42")
    assert isinstance(node, Number)
    assert node.value == 42


def test_parse_float():
    node = parse("3.5")
    assert isinstance(node, Number)
    assert node.value == 3.5


def test_parse_variable():
    node = parse("foo")
    assert isinstance(node, Variable)
    assert node.name == "foo"


def test_parse_simple_addition():
    node = parse("1 + 2")
    assert isinstance(node, BinOp)
    assert node.op == "+"
    assert node.left.value == 1
    assert node.right.value == 2


def test_parse_subtraction():
    node = parse("5 - 3")
    assert node.op == "-"


def test_addition_left_associative():
    # 1 - 2 - 3  ->  (1 - 2) - 3
    node = parse("1 - 2 - 3")
    assert node.op == "-"
    assert isinstance(node.left, BinOp)
    assert node.left.op == "-"
    assert node.left.left.value == 1
    assert node.left.right.value == 2
    assert node.right.value == 3


def test_multiplicative_ops():
    for text, op in [("2*3", "*"), ("6/2", "/"), ("7//2", "//"), ("7%2", "%")]:
        node = parse(text)
        assert isinstance(node, BinOp)
        assert node.op == op


def test_precedence_mult_over_add():
    # 1 + 2 * 3  ->  1 + (2 * 3)
    node = parse("1 + 2 * 3")
    assert node.op == "+"
    assert node.left.value == 1
    assert isinstance(node.right, BinOp)
    assert node.right.op == "*"


def test_power_right_associative():
    # 2 ** 3 ** 2  ->  2 ** (3 ** 2)
    node = parse("2 ** 3 ** 2")
    assert node.op == "**"
    assert node.left.value == 2
    assert isinstance(node.right, BinOp)
    assert node.right.op == "**"
    assert node.right.left.value == 3
    assert node.right.right.value == 2


def test_power_over_mult():
    # 2 * 3 ** 2  ->  2 * (3 ** 2)
    node = parse("2 * 3 ** 2")
    assert node.op == "*"
    assert isinstance(node.right, BinOp)
    assert node.right.op == "**"


def test_unary_minus():
    node = parse("-5")
    assert isinstance(node, UnaryOp)
    assert node.op == "-"
    assert node.operand.value == 5


def test_double_unary_minus():
    node = parse("--5")
    assert isinstance(node, UnaryOp)
    assert isinstance(node.operand, UnaryOp)
    assert node.operand.operand.value == 5


def test_unary_binds_tighter_than_power_base():
    # -2 ** 2 : unary parses first as base, then power
    node = parse("-2 ** 2")
    assert isinstance(node, BinOp)
    assert node.op == "**"
    assert isinstance(node.left, UnaryOp)


def test_parenthesized_expr():
    # (1 + 2) * 3
    node = parse("(1 + 2) * 3")
    assert node.op == "*"
    assert isinstance(node.left, BinOp)
    assert node.left.op == "+"
    assert node.right.value == 3


def test_function_call_no_args():
    node = parse("rand()")
    assert isinstance(node, FunctionCall)
    assert node.name == "rand"
    assert node.args == []


def test_function_call_one_arg():
    node = parse("sqrt(9)")
    assert isinstance(node, FunctionCall)
    assert node.name == "sqrt"
    assert len(node.args) == 1
    assert node.args[0].value == 9


def test_function_call_multiple_args():
    node = parse("max(1, 2, 3)")
    assert isinstance(node, FunctionCall)
    assert node.name == "max"
    assert len(node.args) == 3
    assert [a.value for a in node.args] == [1, 2, 3]


def test_function_call_with_expr_args():
    node = parse("pow(2 + 1, 3)")
    assert isinstance(node, FunctionCall)
    assert isinstance(node.args[0], BinOp)


def test_assignment():
    node = parse("x = 5")
    assert isinstance(node, Assignment)
    assert node.name == "x"
    assert node.expr.value == 5


def test_assignment_with_expression():
    node = parse("y = 2 * 3 + 1")
    assert isinstance(node, Assignment)
    assert node.name == "y"
    assert isinstance(node.expr, BinOp)


def test_nested_parens():
    node = parse("((7))")
    assert isinstance(node, Number)
    assert node.value == 7


def test_parse_pos_tracked():
    node = parse("1 + 2")
    assert node.pos == 2  # position of the '+' operator


def test_parser_class_direct():
    p = Parser(tokenize("1 + 2"))
    node = p.parse()
    assert isinstance(node, BinOp)


def test_trailing_token_raises():
    with pytest.raises(ParseError):
        parse("1 2")


def test_missing_operand_raises():
    with pytest.raises(ParseError):
        parse("1 +")


def test_unclosed_paren_raises():
    with pytest.raises(ParseError):
        parse("(1 + 2")


def test_unmatched_rparen_raises():
    with pytest.raises(ParseError):
        parse(")")


def test_missing_rparen_in_call_raises():
    with pytest.raises(ParseError):
        parse("f(1, 2")


def test_empty_input_raises():
    with pytest.raises(ParseError):
        parse("")


def test_parse_error_carries_pos():
    with pytest.raises(ParseError) as exc:
        parse("1 2")
    assert exc.value.pos == 2


def test_consume_wrong_type_raises():
    p = Parser(tokenize("1"))
    with pytest.raises(ParseError):
        p.consume("PLUS")


def test_parseerror_message_and_pos():
    err = ParseError("bad", 3)
    assert err.pos == 3
    assert str(err) == "bad"
