# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / nested_brackets



本文件实现 nested_brackets 相关的算法功能。

"""



# is_balanced 函数实现

def is_balanced(s: str) -> bool:

    """

    >>> is_balanced("")

    True

    >>> is_balanced("()")

    True

    >>> is_balanced("[]")

    True

    >>> is_balanced("{}")

    True

    >>> is_balanced("()[]{}")

    True

    >>> is_balanced("(())")

    True

    >>> is_balanced("[[")

    False

    >>> is_balanced("([{}])")

    True

    >>> is_balanced("(()[)]")

    False

    >>> is_balanced("([)]")

    False

    >>> is_balanced("[[()]]")

    True

    >>> is_balanced("(()(()))")

    True

    >>> is_balanced("]")

    False

    >>> is_balanced("Life is a bowl of cherries.")

    True

    >>> is_balanced("Life is a bowl of che{}ies.")

    True

    >>> is_balanced("Life is a bowl of che}{ies.")

    False

    """

    open_to_closed = {"{": "}", "[": "]", "(": ")"}

    stack = []

    for symbol in s:

    # 遍历循环

        if symbol in open_to_closed:

    # 条件判断

            stack.append(symbol)

        elif symbol in open_to_closed.values() and (

            not stack or open_to_closed[stack.pop()] != symbol

        ):

            return False

    # 返回结果

    return not stack  # stack should be empty

    # 返回结果







# main 函数实现

def main():

    s = input("Enter sequence of brackets: ")

    print(f"'{s}' is {'' if is_balanced(s) else 'not '}balanced.")





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()

    main()

