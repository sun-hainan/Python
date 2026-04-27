# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / sentinel_linear_search



本文件实现 sentinel_linear_search 相关的算法功能。

"""



# sentinel_linear_search 函数实现

def sentinel_linear_search(sequence, target):

    """Pure implementation of sentinel linear search algorithm in Python



    :param sequence: some sequence with comparable items

    :param target: item value to search

    :return: index of found item or None if item is not found



    Examples:

    >>> sentinel_linear_search([0, 5, 7, 10, 15], 0)

    0



    >>> sentinel_linear_search([0, 5, 7, 10, 15], 15)

    4



    >>> sentinel_linear_search([0, 5, 7, 10, 15], 5)

    1



    >>> sentinel_linear_search([0, 5, 7, 10, 15], 6)



    """

    sequence.append(target)



    index = 0

    while sequence[index] != target:

    # 条件循环

        index += 1



    sequence.pop()



    if index == len(sequence):

    # 条件判断

        return None

    # 返回结果



    return index

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    user_input = input("Enter numbers separated by comma:\n").strip()

    sequence = [int(item) for item in user_input.split(",")]



    target_input = input("Enter a single number to be found in the list:\n")

    target = int(target_input)

    result = sentinel_linear_search(sequence, target)

    if result is not None:

    # 条件判断

        print(f"{target} found at positions: {result}")

    else:

        print("Not found")

