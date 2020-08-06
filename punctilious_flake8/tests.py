import ast
from typing import Any

import pytest

from punctilious_flake8 import TrivialIfFinder, PartialEvaluator

EXAMPLE_IF_TRUE = 'if True: ...'


def parse_expr(expr: str) -> ast.AST:
    """
    Returns the ast node corresponding to the given expression
    """
    module_expr = ast.parse(expr)
    return module_expr.body[0]


def check_deterministic(expr: str) -> bool:
    node = parse_expr(expr)
    try:
        value = eval(expr)
    except Exception as e:
        pass
    else:
        assert value == PartialEvaluator().visit(node)
    return PartialEvaluator.is_deterministic(node)


def partial_eval(expr: str) -> Any:
    return PartialEvaluator().visit(parse_expr(expr))


@pytest.mark.parametrize('statement', [
    'True',
    'True or False',
    'False or True',
    'True and False',
    'False and True',
    'not True',
    'not False',
    'not 1',
    'True or a == 2',
    '1 == 1',
    '1 == 2',
    'a and 1 == 2',
    'a or 1 == 1',
    '1 == 1 or a',
    '"foo"',
    'x == "foo" or "bar"',
    '1 in (1,)',
    '1 in (1, x)',
    '1 < 0',
    '1 <= 0',
    '1 >= 0',
    '1 != 0',
    '1 < 0',
    '1 > 0',
    '1 == 1',
    '1 <= 1',
    '1 >= 1',
    '1 != 1',
    '1 < 1',
    '1 > 1',
    # '-(1 + 1)', # TODO
])
def test_deterministic(statement):
    assert check_deterministic(statement)

@pytest.mark.parametrize('statement', [
    'not a',
    'a == 2',
    'True and a == 2',
    'a or 1 == 2',
    'x == "foo" or x == "bar"',
    'x in (1.0, 2)',
    '1 in x',
    '1 in (x,)',
])
def test_not_deterministic(statement):
    assert not check_deterministic(statement)




# def test():
#     TrivialIfFinder().generic_visit(ast.parse(EXAMPLE_IF_TRUE))
