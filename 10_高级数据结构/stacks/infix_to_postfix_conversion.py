# -*- coding: utf-8 -*-

"""

算法实现：stacks / infix_to_postfix_conversion



本文件实现 infix_to_postfix_conversion 相关的算法功能。

"""



from typing import Literal



from .balanced_parentheses import balanced_parentheses

from .stack import Stack



PRECEDENCES: dict[str, int] = {

    "+": 1,

    "-": 1,

    "*": 2,

    "/": 2,

    "^": 3,

}

ASSOCIATIVITIES: dict[str, Literal["LR", "RL"]] = {

    "+": "LR",

    "-": "LR",

    "*": "LR",

    "/": "LR",

    "^": "RL",

}







# =============================================================================

# 算法模块：precedence

# =============================================================================

def precedence(char: str) -> int:

    # precedence function



    # precedence function

    """

    Return integer value representing an operator's precedence, or

    order of operation.

    https://en.wikipedia.org/wiki/Order_of_operations

    """

    return PRECEDENCES.get(char, -1)





def associativity(char: str) -> Literal["LR", "RL"]:

    # associativity function



    # associativity function

    """

    Return the associativity of the operator `char`.

    https://en.wikipedia.org/wiki/Operator_associativity

    """

    return ASSOCIATIVITIES[char]





def infix_to_postfix(expression_str: str) -> str:

    # infix_to_postfix function



    # infix_to_postfix function

    """

    >>> infix_to_postfix("(1*(2+3)+4))")

    Traceback (most recent call last):

        ...

    ValueError: Mismatched parentheses

    >>> infix_to_postfix("")

    ''

    >>> infix_to_postfix("3+2")

    '3 2 +'

    >>> infix_to_postfix("(3+4)*5-6")

    '3 4 + 5 * 6 -'

    >>> infix_to_postfix("(1+2)*3/4-5")

    '1 2 + 3 * 4 / 5 -'

    >>> infix_to_postfix("a+b*c+(d*e+f)*g")

    'a b c * + d e * f + g * +'

    >>> infix_to_postfix("x^y/(5*z)+2")

    'x y ^ 5 z * / 2 +'

    >>> infix_to_postfix("2^3^2")

    '2 3 2 ^ ^'

    """

    if not balanced_parentheses(expression_str):

        raise ValueError("Mismatched parentheses")

    stack: Stack[str] = Stack()

    postfix = []

    for char in expression_str:

        if char.isalpha() or char.isdigit():

            postfix.append(char)

        elif char == "(":

            stack.push(char)

        elif char == ")":

            while not stack.is_empty() and stack.peek() != "(":

                postfix.append(stack.pop())

            stack.pop()

        else:

            while True:

                if stack.is_empty():

                    stack.push(char)

                    break



                char_precedence = precedence(char)

                tos_precedence = precedence(stack.peek())



                if char_precedence > tos_precedence:

                    stack.push(char)

                    break

                if char_precedence < tos_precedence:

                    postfix.append(stack.pop())

                    continue

                # Precedences are equal

                if associativity(char) == "RL":

                    stack.push(char)

                    break

                postfix.append(stack.pop())



    while not stack.is_empty():

        postfix.append(stack.pop())

    return " ".join(postfix)





if __name__ == "__main__":

    from doctest import testmod



    testmod()

    expression = "a+b*(c^d-e)^(f+g*h)-i"



    print("Infix to Postfix Notation demonstration:\n")

    print("Infix notation: " + expression)

    print("Postfix notation: " + infix_to_postfix(expression))

