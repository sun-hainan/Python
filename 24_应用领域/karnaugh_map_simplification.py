# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / karnaugh_map_simplification



本文件实现 karnaugh_map_simplification 相关的算法功能。

"""



# simplify_kmap 函数实现

def simplify_kmap(kmap: list[list[int]]) -> str:

    """

    Simplify the Karnaugh map.

    >>> simplify_kmap(kmap=[[0, 1], [1, 1]])

    "A'B + AB' + AB"

    >>> simplify_kmap(kmap=[[0, 0], [0, 0]])

    ''

    >>> simplify_kmap(kmap=[[0, 1], [1, -1]])

    "A'B + AB' + AB"

    >>> simplify_kmap(kmap=[[0, 1], [1, 2]])

    "A'B + AB' + AB"

    >>> simplify_kmap(kmap=[[0, 1], [1, 1.1]])

    "A'B + AB' + AB"

    >>> simplify_kmap(kmap=[[0, 1], [1, 'a']])

    "A'B + AB' + AB"

    """

    simplified_f = []

    for a, row in enumerate(kmap):

    # 遍历循环

        for b, item in enumerate(row):

    # 遍历循环

            if item:

    # 条件判断

                term = ("A" if a else "A'") + ("B" if b else "B'")

                simplified_f.append(term)

    return " + ".join(simplified_f)

    # 返回结果







# main 函数实现

def main() -> None:

    """

    Main function to create and simplify a K-Map.



    >>> main()

    [0, 1]

    [1, 1]

    Simplified Expression:

    A'B + AB' + AB

    """

    kmap = [[0, 1], [1, 1]]



    # Manually generate the product of [0, 1] and [0, 1]



    for row in kmap:

    # 遍历循环

        print(row)



    print("Simplified Expression:")

    print(simplify_kmap(kmap))





if __name__ == "__main__":

    # 条件判断

    main()

    print(f"{simplify_kmap(kmap=[[0, 1], [1, 1]]) = }")

