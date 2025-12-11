import ast
import operator as op

def solve(input_str):
    """
    Safely evaluates a string containing a simple arithmetic expression.
    Supports addition, subtraction, multiplication, and division.
    """
    # Supported operators mapping
    _operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
    }

    def _eval_node(node):
        """Recursively evaluates an AST node."""
        # Handle numbers (compatible with Python < 3.8 and >= 3.8)
        if isinstance(node, (ast.Num, ast.Constant)):
            return node.n if isinstance(node, ast.Num) else node.value
        # Handle binary operations
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_func = _operators.get(type(node.op))
            if op_func is None:
                raise TypeError(f"Unsupported operator: {type(node.op)}")
            return op_func(left, right)
        # Handle other cases
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

    try:
        # Parse the input string into an AST
        node = ast.parse(input_str.strip(), mode='eval').body
        return _eval_node(node)
    except (TypeError, KeyError, SyntaxError, ValueError, ZeroDivisionError) as e:
        # Catch potential errors during parsing or evaluation
        return f"Error: Invalid or unsupported expression. Details: {e}"