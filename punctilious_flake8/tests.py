import ast

from punctilious_flake8 import TrivialIfFinder, PartialEvaluator

EXAMPLE_IF_TRUE = 'if True: ...'


def parse_expr(expr: str) -> ast.AST:
    """
    Returns the ast node corresponding to the given expression
    """
    module_expr = ast.parse(expr)
    return module_expr.body[0]


def is_deterministic_constant_statement(expr: str) -> bool:
    return PartialEvaluator.is_deterministic(parse_expr(expr))

def test_DeterministicConstantStatement():
    assert is_deterministic_constant_statement('True')
    assert is_deterministic_constant_statement('True or False')
    assert is_deterministic_constant_statement('False or True')
    assert is_deterministic_constant_statement('True and False')
    assert is_deterministic_constant_statement('False and True')
    assert not is_deterministic_constant_statement('a == 2')
    assert not is_deterministic_constant_statement('True and a == 2')
    assert is_deterministic_constant_statement('True or a == 2')
    assert is_deterministic_constant_statement('1 == 1')
    assert is_deterministic_constant_statement('1 == 2')
    assert is_deterministic_constant_statement('a and 1 == 2')
    assert not is_deterministic_constant_statement('a or 1 == 2')
    assert is_deterministic_constant_statement('a or 1 == 1')
    assert is_deterministic_constant_statement('1 == 1 or a')
    assert is_deterministic_constant_statement('"foo"')
    assert is_deterministic_constant_statement('x == "foo" or "bar"')
    assert not is_deterministic_constant_statement('x == "foo" or x == "bar"')
    assert not is_deterministic_constant_statement('x in (1.0, 2)')
    assert is_deterministic_constant_statement('1 in (1,)')
    assert is_deterministic_constant_statement('1 in (1, x)')
    assert not is_deterministic_constant_statement('1 in x')
    assert not is_deterministic_constant_statement('1 in (x,)')
    assert is_deterministic_constant_statement('1 < 0')
    
    


# def test():
#     TrivialIfFinder().generic_visit(ast.parse(EXAMPLE_IF_TRUE))
