# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / wave_string

本文件实现 wave_string 相关的算法功能。
"""

from typing import List


def wave_string_simple(s: str) -> str:
    """
    简单波浪：辅音放奇数位，元音放偶数位

    参数：
        s: 输入字符串

    返回：波浪形字符串
    """
    vowels = set('aeiouAEIOU')

    consonants = []
    vowel_list = []

    for char in s:
        if char.isalpha():
            if char in vowels:
                vowel_list.append(char)
            else:
                consonants.append(char)

    result = []
    i, j = 0, 0

    for idx, char in enumerate(s):
        if char.isalpha():
            if char in vowels:
                if j < len(vowel_list):
                    result.append(vowel_list[j])
                    j += 1
                else:
                    result.append('_')
            else:
                if i < len(consonants):
                    result.append(consonants[i])
                    i += 1
                else:
                    result.append('_')
        else:
            result.append(char)

    return ''.join(result)


def wave_string_alt(s: str) -> str:
    """
    交替大小写波浪

    奇数位大写，偶数位小写（或反之）

    参数：
        s: 输入字符串

    返回：交替大小写的波浪字符串
    """
    char_list = list(s)
    n = len(char_list)

    for i in range(n):
        if char_list[i].isalpha():
            if i % 2 == 0:
                char_list[i] = char_list[i].upper()
            else:
                char_list[i] = char_list[i].lower()

    return ''.join(char_list)


def wave_string_height(s: str) -> str:
    """
    按字符高度分组波浪

    大写字母和符号看作"高"，小写字母看作"低"

    参数：
        s: 输入字符串

    返回：波浪形排列
    """
    high = []  # 大写
    low = []   # 小写

    for char in s:
        if char.isupper():
            high.append(char)
        elif char.islower():
            low.append(char)
        else:
            # 非字母字符归入高位
            high.append(char)

    # 交叉排列
    result = []
    i = 0

    while i < len(high) or i < len(low):
        if i < len(high):
            result.append(high[i])
        if i < len(low):
            result.append(low[i])
        i += 1

    return ''.join(result)


def wave_sort_array(arr: List[int]) -> List[int]:
    """
    数组波浪排序

    arr[0] >= arr[1] <= arr[2] >= arr[3] <= ...

    参数：
        arr: 整数数组

    返回：波浪排序后的数组
    """
    n = len(arr)
    arr = arr.copy()

    # 只需保证每个峰的值大于等于相邻的谷
    for i in range(0, n - 1, 2):
        if i + 1 < n and arr[i] < arr[i + 1]:
            arr[i], arr[i + 1] = arr[i + 1], arr[i]

    return arr


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 波浪形字符串测试 ===\n")

    test_strings = [
        "hello",
        "HELLO",
        "HeLLoWoRLD",
        "Python3",
        "aeiou",
        "bcdfg",
    ]

    print("1. 辅音/元音波浪:")
    for s in test_strings:
        result = wave_string_simple(s)
        print(f"  '{s}' -> '{result}'")

    print()

    print("2. 交替大小写波浪:")
    for s in test_strings[:3]:
        result = wave_string_alt(s)
        print(f"  '{s}' -> '{result}'")

    print()

    print("3. 高度波浪:")
    for s in test_strings[:3]:
        result = wave_string_height(s)
        print(f"  '{s}' -> '{result}'")

    print()

    print("4. 数组波浪排序:")
    arrays = [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1], [6, 2, 8, 3, 9, 1]]
    for arr in arrays:
        result = wave_sort_array(arr)
        print(f"  {arr} -> {result}")

    print()
    print("复杂度分析：")
    print("  时间复杂度: O(n)")
    print("  空间复杂度: O(n)")
    print()
    print("说明：")
    print("  - 波浪字符串是字符排序的变体")
    print("  - 实际应用：数据可视化、游戏地图等")
