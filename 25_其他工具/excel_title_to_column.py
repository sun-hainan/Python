# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / excel_title_to_column



本文件实现 excel_title_to_column 相关的算法功能。

"""



# excel_title_to_column 函数实现

def excel_title_to_column(column_title: str) -> int:

    """

    Given a string column_title that represents

    the column title in an Excel sheet, return

    its corresponding column number.



    >>> excel_title_to_column("A")

    1

    >>> excel_title_to_column("B")

    2

    >>> excel_title_to_column("AB")

    28

    >>> excel_title_to_column("Z")

    26

    """

    assert column_title.isupper()

    answer = 0

    index = len(column_title) - 1

    power = 0



    while index >= 0:

    # 条件循环

        value = (ord(column_title[index]) - 64) * pow(26, power)

        answer += value

        power += 1

        index -= 1



    return answer

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()

