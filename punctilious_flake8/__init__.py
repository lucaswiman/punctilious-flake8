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


class Indeterminate(typing.NamedTuple):
    # truthy is None => Indeterminate truth value
    # truthy is True => Indeterminate value, but will be truthy (e.g. ``a or True``)
    # truthy is False => Indeterminate value, but will be falsey (TODO: is this ever possible?).
    truthy: typing.Optional[bool]

def truthy(obj) -> typing.Optional[bool]:
    if isinstance(obj, Indeterminate):
        return obj.truthy
    else:
        return bool(obj)

AST_OP_TO_OPERATOR = {
    ast.Lt: operator.lt,
    ast.Eq: operator.eq,
    ast.Gt: operator.gt,
    ast.GtE: lambda x, y: x >= y,
    ast.LtE: lambda x, y: x <= y,
    ast.NotEq: lambda x, y: x != y,
    ast.Add: operator.add,
    ast.USub: operator.neg,
}

class ISuckError(Exception):
    pass

class PartialEvaluator(ast.NodeVisitor):
    @classmethod
    def is_deterministic(cls, node) -> bool:
        value = cls().visit(node)
        if isinstance(value, Indeterminate):
            return value.truthy is not None
        return True

    def generic_visit(self, node):
        return Indeterminate(truthy=None)

    def visit_BoolOp(self, node):
        values = {self.visit(child) for child in node.values}
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
        op = type(node.op)
        operand = self.visit(node.operand)
        if operand == Indeterminate(truthy=None):
            return operand
        elif op == ast.Not:
            if isinstance(operand, Indeterminate):
                # Negation always returns a boolean value
                return (not operand.truthy)
            else:
                return not operand
        elif op in AST_OP_TO_OPERATOR:
            if isinstance(operand, Indeterminate):
                return (not operand.truthy)
            else:
                return AST_OP_TO_OPERATOR[op](operand)
        else:
            return Indeterminate(truthy=None)

    def visit_Expr(self, node):
        """
        Expr seems to be like a container node with a single attribute `value`.
        """
        return self.visit(node.value)

    def visit_NameConstant(self, node):
        return node.value

    def visit_Compare(self, node):
        comparators = [self.visit(comparator) for comparator in node.comparators]
        objects = [self.visit(node.left), *comparators]
        comparisons = zip(objects, objects[1:])
        comparison_results = []
        for ((left, right), op) in zip(comparisons, node.ops):
            if isinstance(left, Indeterminate) or isinstance(right, Indeterminate):
                comparison_results.append(Indeterminate(truthy=None))
            elif type(op) in AST_OP_TO_OPERATOR:
                comparison_results.append(AST_OP_TO_OPERATOR[type(op)](left, right))
            elif type(op) == ast.In:
                try:
                    if left in right:
                        comparison_results.append(True)
                    elif any(isinstance(elem, Indeterminate) for elem in right):
                        comparison_results.append(Indeterminate(truthy=None))
                    else:
                        comparison_results.append(False)
                except Exception as e:
                    comparison_results.append(Indeterminate(truthy=None))
            elif type(op) == ast.Is:
                if left in (True, False, None) and right in (True, False, None):
                    comparison_results.append(left is right)
                else:
                    comparison_results.append(Indeterminate(truthy=None))
            else:
                comparison_results.append(Indeterminate(truthy=None))
        truth_results = {truthy(result) for result in comparison_results}
        if False in truth_results:
            return False
        elif all(truth_results):
            return True
        else:
            return Indeterminate(truthy=None)

    def visit_BinOp(self, node):
        vals = self.visit(node.left), self.visit(node.right)
        if type(node.op) in AST_OP_TO_OPERATOR:
            op = AST_OP_TO_OPERATOR[type(node.op)]
            if any(isinstance(val, Indeterminate) for val in vals):
                return Indeterminate(truthy=None)
            else:
                return op(*vals)
        return Indeterminate(truthy=None)

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

    def visit_List(self, node):
        return [self.visit(child) for child in node.elts]

    def visit_Set(self, node):
        return {self.visit(child) for child in node.elts}

    def visit_Dict(self, node):
        return {self.visit(key): self.visit(value) for key, value in zip(node.keys, node.values)}


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
        if PartialEvaluator.is_deterministic(node.test):
            self.stupid_if_statements.append(node)


class Plugin:
    name = "punctilious-flake8"
    version = __version__

    def __init__(self, tree):
        self.tree = tree

    def run(self):
        finder = TrivialIfFinder()
        try:
            finder.visit(self.tree)
        except ISuckError as e:
            node = e.node
            yield (
                node.lineno,
                node.col_offset,
                "PNC200 I suck",
                type(self),
            )
        else:
            for node in finder.stupid_if_statements:
                yield (
                    node.lineno,
                    node.col_offset,
                    "PNC100 if statement always evaluates to the same value.",
                    type(self),
                )
