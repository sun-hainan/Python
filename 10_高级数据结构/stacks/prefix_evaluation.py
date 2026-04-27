# -*- coding: utf-8 -*-
"""
算法实现：stacks / prefix_evaluation

本文件实现 prefix_evaluation 相关的算法功能。
"""

operators = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
}



# =============================================================================
# 算法模块：is_operand
# =============================================================================
def is_operand(c):
    # is_operand function

    # is_operand function
    """
    Return True if the given char c is an operand, e.g. it is a number

    >>> is_operand("1")
    True
    >>> is_operand("+")
    False
    """
    return c.isdigit()


def evaluate(expression):
    # evaluate function

    # evaluate function
    """
    Evaluate a given expression in prefix notation.
    Asserts that the given expression is valid.

    >>> evaluate("+ 9 * 2 6")
    21
    >>> evaluate("/ * 10 2 + 4 1 ")
    4.0
    >>> evaluate("2")
    2
    >>> evaluate("+ * 2 3 / 8 4")
    8.0
    """
    stack = []

    # iterate over the string in reverse order
    for c in expression.split()[::-1]:
        # push operand to stack
        if is_operand(c):
            stack.append(int(c))

        else:
            # pop values from stack can calculate the result
            # push the result onto the stack again
            o1 = stack.pop()
            o2 = stack.pop()
            stack.append(operators[c](o1, o2))

    return stack.pop()


def evaluate_recursive(expression: list[str]):
    # evaluate_recursive function

    # evaluate_recursive function
    """
    Alternative recursive implementation

    >>> evaluate_recursive(['2'])
    2
    >>> expression = ['+', '*', '2', '3', '/', '8', '4']
    >>> evaluate_recursive(expression)
    8.0
    >>> expression
    []
    >>> evaluate_recursive(['+', '9', '*', '2', '6'])
    21
    >>> evaluate_recursive(['/', '*', '10', '2', '+', '4', '1'])
    4.0
    """

    op = expression.pop(0)
    if is_operand(op):
        return int(op)

    operation = operators[op]

    a = evaluate_recursive(expression)
    b = evaluate_recursive(expression)
    return operation(a, b)


# Driver code
if __name__ == "__main__":
    test_expression = "+ 9 * 2 6"
    print(evaluate(test_expression))

    test_expression = "/ * 10 2 + 4 1 "
    print(evaluate(test_expression))
