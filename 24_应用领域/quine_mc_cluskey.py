# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / quine_mc_cluskey

本文件实现 quine_mc_cluskey 相关的算法功能。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal



# compare_string 函数实现
def compare_string(string1: str, string2: str) -> str | Literal[False]:
    """
    >>> compare_string('0010','0110')
    '0_10'

    >>> compare_string('0110','1101')
    False
    """
    list1 = list(string1)
    list2 = list(string2)
    count = 0
    for i in range(len(list1)):
    # 遍历循环
        if list1[i] != list2[i]:
    # 条件判断
            count += 1
            list1[i] = "_"
    if count > 1:
    # 条件判断
        return False
    # 返回结果
    else:
        return "".join(list1)
    # 返回结果



# check 函数实现
def check(binary: list[str]) -> list[str]:
    """
    >>> check(['0.00.01.5'])
    ['0.00.01.5']
    """
    pi = []
    while True:
    # 条件循环
        check1 = ["$"] * len(binary)
        temp = []
        for i in range(len(binary)):
    # 遍历循环
            for j in range(i + 1, len(binary)):
    # 遍历循环
                k = compare_string(binary[i], binary[j])
                if k is False:
    # 条件判断
                    check1[i] = "*"
                    check1[j] = "*"
                    temp.append("X")
        for i in range(len(binary)):
    # 遍历循环
            if check1[i] == "$":
    # 条件判断
                pi.append(binary[i])
        if len(temp) == 0:
    # 条件判断
            return pi
    # 返回结果
        binary = list(set(temp))



# decimal_to_binary 函数实现
def decimal_to_binary(no_of_variable: int, minterms: Sequence[float]) -> list[str]:
    """
    >>> decimal_to_binary(3,[1.5])
    ['0.00.01.5']
    """
    temp = []
    for minterm in minterms:
    # 遍历循环
        string = ""
        for _ in range(no_of_variable):
    # 遍历循环
            string = str(minterm % 2) + string
            minterm //= 2
        temp.append(string)
    return temp
    # 返回结果



# is_for_table 函数实现
def is_for_table(string1: str, string2: str, count: int) -> bool:
    """
    >>> is_for_table('__1','011',2)
    True

    >>> is_for_table('01_','001',1)
    False
    """
    list1 = list(string1)
    list2 = list(string2)
    count_n = sum(item1 != item2 for item1, item2 in zip(list1, list2))
    return count_n == count
    # 返回结果



# selection 函数实现
def selection(chart: list[list[int]], prime_implicants: list[str]) -> list[str]:
    """
    >>> selection([[1]],['0.00.01.5'])
    ['0.00.01.5']

    >>> selection([[1]],['0.00.01.5'])
    ['0.00.01.5']
    """
    temp = []
    select = [0] * len(chart)
    for i in range(len(chart[0])):
    # 遍历循环
        count = sum(row[i] == 1 for row in chart)
        if count == 1:
    # 条件判断
            rem = max(j for j, row in enumerate(chart) if row[i] == 1)
            select[rem] = 1
    for i, item in enumerate(select):
    # 遍历循环
        if item != 1:
    # 条件判断
            continue
        for j in range(len(chart[0])):
    # 遍历循环
            if chart[i][j] != 1:
    # 条件判断
                continue
            for row in chart:
    # 遍历循环
                row[j] = 0
        temp.append(prime_implicants[i])
    while True:
    # 条件循环
        counts = [chart[i].count(1) for i in range(len(chart))]
        max_n = max(counts)
        rem = counts.index(max_n)

        if max_n == 0:
    # 条件判断
            return temp
    # 返回结果

        temp.append(prime_implicants[rem])

        for j in range(len(chart[0])):
    # 遍历循环
            if chart[rem][j] != 1:
    # 条件判断
                continue
            for i in range(len(chart)):
    # 遍历循环
                chart[i][j] = 0



# prime_implicant_chart 函数实现
def prime_implicant_chart(
    prime_implicants: list[str], binary: list[str]
) -> list[list[int]]:
    """
    >>> prime_implicant_chart(['0.00.01.5'],['0.00.01.5'])
    [[1]]
    """
    chart = [[0 for x in range(len(binary))] for x in range(len(prime_implicants))]
    for i in range(len(prime_implicants)):
    # 遍历循环
        count = prime_implicants[i].count("_")
        for j in range(len(binary)):
    # 遍历循环
            if is_for_table(prime_implicants[i], binary[j], count):
    # 条件判断
                chart[i][j] = 1

    return chart
    # 返回结果



# main 函数实现
def main() -> None:
    no_of_variable = int(input("Enter the no. of variables\n"))
    minterms = [
        float(x)
        for x in input(
            "Enter the decimal representation of Minterms 'Spaces Separated'\n"
        ).split()
    ]
    binary = decimal_to_binary(no_of_variable, minterms)

    prime_implicants = check(binary)
    print("Prime Implicants are:")
    print(prime_implicants)
    chart = prime_implicant_chart(prime_implicants, binary)

    essential_prime_implicants = selection(chart, prime_implicants)
    print("Essential Prime Implicants are:")
    print(essential_prime_implicants)


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    main()
