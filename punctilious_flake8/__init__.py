import ast
import operator
import typing

__version__ = '0.0.01'


def function(arg):
    if False:  # foo
        pass

    if arg == 1 or 2:  # foo
        pass
    if False and arg in (1, 2):  # foo
        pass
    if True or arg in (1, 2):  # foo
        pass


# Walk the ast and evaluate if statements for whether their arguments are determined by literals.
# Based off https://github.com/JBKahn/flake8-debugger/blob/master/flake8_debugger.py

class TrivialIfFinder(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.stupid_if_statements = []

    # def visit(self, node):
    #     breakpoint()
    #     return super().visit(node)

    def visit_If(self, node):
        if DeterministicConstantStatement.is_deterministic(node.test):
            self.stupid_if_statements.append(node)
        breakpoint()


class Indeterminate(typing.NamedTuple):
    # truthy is None => Indeterminate truth value
    # truthy is True => Indeterminate value, but will be truthy (e.g. ``a or True``)
    # truthy is False => Indeterminate value, but will be falsey (TODO: is this ever possible?).
    truthy: typing.Optional[bool]
    

ValueDetermination = typing.Union[typing.Type[Indeterminate], bool]

AST_OP_TO_OPERATOR = {
    ast.Lt: operator.lt,
    ast.Eq: operator.eq,
    ast.Gt: operator.gt,
    ast.GtE: lambda x, y: x >= y,
    ast.LtE: lambda x, y: x <= y,
    ast.NotEq: lambda x, y: x != y,
}

class PartialEvaluator(ast.NodeVisitor):
    @classmethod
    def is_deterministic(cls, node) -> bool:
        value = cls().visit(node)
        if isinstance(value, Indeterminate):
            return value.truthy is not None
        return True

    # def visit(self, node) -> ValueDetermination:
    #     ret = super().visit(node)
    #     if ret is Indeterminate:
    #         return False
    #     else:
    #         return True

    def generic_visit(self, node):
        breakpoint()

    def visit_BoolOp(self, node):
        values: List[ValueDetermination] = {self.visit(child) for child in node.values}
        if isinstance(node.op, ast.Or):
            seen_indeterminate = False
            for value in values:
                if isinstance(value, Indeterminate):
                    if value.truthy is True:
                        return value
                    elif value.truthy is None:
                        seen_indeterminate = True
                elif value:
                    return Indeterminate(truthy=True) if seen_indeterminate else value
            if seen_indeterminate:
                return Indeterminate(truthy=None)
            else:
                return values[-1]
        elif isinstance(node.op, ast.And):
            if not all(values) or Indeterminate(truthy=False) in values:
                # x and y and z always returns False if any of the arguments are Falsey.
                return False
            elif Indeterminate(truthy=None) in values:
                return Indeterminate(truthy=None)
            else:
                # All values are truthy. The last one is returned as a value.
                return values[-1]
        else:  # TODO: verify this is exhaustive
            return Indeterminate(truthy=None)

    def visit_UnaryOp(self, node):
        op = node.op
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            if operand == Indeterminate(truthy=None):
                return operand
            elif isinstance(operand, Indeterminate):
                # Negation always returns a boolean value
                return (not operand.truthy)
            else:
                return not operand
        else:
            breakpoint()

    def visit_Expr(self, node):
        """
        Expr seems to be like a container node with a single attribute `value`.
        """
        return self.visit(node.value)

    def visit_NameConstant(self, node):
        return node.value

    def visit_Compare(self, node):
        left = self.visit(node.left)
        # TODO: handle multiple comparators or ops
        [comparator] = [self.visit(comparator) for comparator in node.comparators]
        if isinstance(left, Indeterminate) or isinstance(comparator, Indeterminate):
            return Indeterminate(truthy=None)
        [op] = node.ops
        if type(op) in AST_OP_TO_OPERATOR:
            return AST_OP_TO_OPERATOR[type(op)](left, comparator)
        elif type(op) == ast.In:
            try:
                if left in comparator:
                    return True
                elif any(isinstance(c, Indeterminate) for c in comparator):
                    return Indeterminate(truthy=None)
                else:
                    return False
            except Exception as e:
                return Indeterminate(truthy=None)
        else:
            breakpoint()

    def visit_Num(self, node):
        return node.n

    def visit_Str(self, node):
        return node.s

    def visit_Name(self, node):
        """
        Name is refers to a variable name; could be anything at runtime.
        """
        return Indeterminate(truthy=None)

    def visit_Tuple(self, node):
        # TODO: what is node.ctx?
        return tuple(self.visit(child) for child in node.elts)


class Plugin:
    name = "punctilious-flake8"
    version = __version__

    def __init__(self, tree):
        self.tree = tree

    def run(self):
        if True:
            args.append(self.tree)
            with open('/tmp/punctilious-args.pkl', 'wb') as f:
                f.write(pickle.dumps(args))
        yield from []
