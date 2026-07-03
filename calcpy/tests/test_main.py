import pytest

from main import Token, LexError, tokenize


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
