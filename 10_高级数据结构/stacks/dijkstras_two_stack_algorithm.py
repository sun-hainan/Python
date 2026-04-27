# -*- coding: utf-8 -*-

"""

算法实现：stacks / dijkstras_two_stack_algorithm



本文件实现 dijkstras_two_stack_algorithm 相关的算法功能。

"""



__author__ = "Alexander Joslin"



import operator as op



from .stack import Stack







# =============================================================================

# 算法模块：dijkstras_two_stack_algorithm

# =============================================================================

def dijkstras_two_stack_algorithm(equation: str) -> int:

    # dijkstras_two_stack_algorithm function



    # dijkstras_two_stack_algorithm function

    """

    DocTests

    >>> dijkstras_two_stack_algorithm("(5 + 3)")

    8

    >>> dijkstras_two_stack_algorithm("((9 - (2 + 9)) + (8 - 1))")

    5

    >>> dijkstras_two_stack_algorithm("((((3 - 2) - (2 + 3)) + (2 - 4)) + 3)")

    -3



    :param equation: a string

    :return: result: an integer

    """

    operators = {"*": op.mul, "/": op.truediv, "+": op.add, "-": op.sub}



    operand_stack: Stack[int] = Stack()

    operator_stack: Stack[str] = Stack()



    for i in equation:

        if i.isdigit():

            # RULE 1

            operand_stack.push(int(i))

        elif i in operators:

            # RULE 2

            operator_stack.push(i)

        elif i == ")":

            # RULE 4

            opr = operator_stack.peek()

            operator_stack.pop()

            num1 = operand_stack.peek()

            operand_stack.pop()

            num2 = operand_stack.peek()

            operand_stack.pop()



            total = operators[opr](num2, num1)

            operand_stack.push(total)



    # RULE 5

    return operand_stack.peek()





if __name__ == "__main__":

    equation = "(5 + ((4 * 2) * (2 + 3)))"

    # answer = 45

    print(f"{equation} = {dijkstras_two_stack_algorithm(equation)}")

