# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / strip

本文件实现 strip 相关的算法功能。
"""

def strip(user_string: str, characters: str = " \t\n\r") -> str:
    """
    去除字符串首部和尾部的指定字符（默认为空白字符）

    参数:
        user_string (str): 输入的原始字符串
        characters (str, optional): 要去除的字符集合（默认是空白字符）

    返回:
        str: 去除首尾字符后的字符串

    示例:
        >>> strip("   hello   ")
        'hello'
        >>> strip("...world...", ".")
        'world'
        >>> strip("123hello123", "123")
        'hello'
        >>> strip("")
        ''
    """

    # 初始化起始位置（从头）和结束位置（从尾）
    start = 0
    end = len(user_string)

    # 从左向右跳过要去除的字符
    while start < end and user_string[start] in characters:
        start += 1

    # 从右向左跳过要去除的字符
    while end > start and user_string[end - 1] in characters:
        end -= 1

    # 返回切片结果（不修改原字符串）
    return user_string[start:end]


if __name__ == "__main__":
    # 验证基本功能
    assert strip("   hello   ") == "hello"
    assert strip("...world...", ".") == "world"
    assert strip("123hello123", "123") == "hello"
    assert strip("") == ""

    # 验证空白字符默认行为
    assert strip("\t\thello\n\n") == "hello"
    assert strip("  hello world  ") == "hello world"

    # 验证自定义字符
    assert strip("***hello***", "*") == "hello"
    assert strip("abchelloabc", "abc") == "hello"

    print("strip 函数测试全部通过！")
