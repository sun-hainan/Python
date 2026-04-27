# -*- coding: utf-8 -*-
"""
算法实现：27_整数与FFT / integer_division

本文件实现 integer_division 相关的算法功能。
"""

from typing import Tuple


def divide_large_int(dividend: int, divisor: int) -> Tuple[int, int]:
    """
    大整数除法

    返回：(商, 余数)

    参数：
        dividend: 被除数
        divisor: 除数

    返回：(商, 余数)
    """
    if divisor == 0:
        raise ValueError("除数不能为0")

    if dividend < divisor:
        return 0, dividend

    quotient = dividend // divisor
    remainder = dividend % divisor

    return quotient, remainder


def string_division(dividend_str: str, divisor_str: str) -> Tuple[str, str]:
    """
    字符串形式的大整数除法

    用于处理超出Python整数范围的大数

    参数：
        dividend_str: 被除数字符串
        divisor_str: 除数字符串

    返回：(商字符串, 余数字符串)
    """
    if len(divisor_str) == 1 and divisor_str == "0":
        raise ValueError("除数不能为0")

    # 转换为整数处理
    divisor_int = int(divisor_str)
    n = len(dividend_str)
    result = []
    remainder = 0

    for i in range(n):
        # 当前处理的数字
        digit = int(dividend_str[i])
        current = remainder * 10 + digit

        # 估计商
        q = current // divisor_int
        result.append(str(q))

        # 更新余数
        remainder = current - q * divisor_int

    # 移除前导零
    while len(result) > 1 and result[0] == "0":
        result.pop(0)

    quotient_str = "".join(result) if result else "0"
    remainder_str = str(remainder)

    return quotient_str, remainder_str


def binary_division(dividend: int, divisor: int) -> Tuple[int, int]:
    """
    二进制除法（用于硬件实现）

    参数：
        dividend: 被除数（正整数）
        divisor: 除数（正整数）

    返回：(商, 余数)
    """
    if divisor == 0:
        raise ValueError("除数不能为0")

    if dividend < divisor:
        return 0, dividend

    quotient = 0
    remainder = 0
    dividend_bits = dividend.bit_length()
    divisor_bits = divisor.bit_length()

    for i in range(dividend_bits - 1, -1, -1):
        # 左移remainder，并将dividend的当前位填入
        remainder = (remainder << 1) | ((dividend >> i) & 1)

        if remainder >= divisor:
            quotient |= (1 << i)
            remainder -= divisor

    return quotient, remainder


def long_division(dividend_str: str, divisor_str: str) -> Tuple[str, str]:
    """
    长除法算法（逐位试商）

    这是手工除法的程序化实现

    示例：12345 / 23
        - 从最高位开始：1 < 23，商0，余1
        - 连接下一位：12 < 23，商0，余12
        - 连接下一位：124 > 23，商5，余124-5*23=9
        - 连接下一位：93 >= 23，商4，余93-4*23=1
        - 结果：12345 / 23 = 537 余 1
    """
    if divisor_str == "0":
        raise ValueError("除数不能为0")

    # 去除前导零
    dividend_str = dividend_str.lstrip('0')
    divisor_str = divisor_str.lstrip('0')

    if not dividend_str:
        return "0", "0"
    if not divisor_str:
        return "0", dividend_str

    # 比较大小
    if len(divisor_str) > len(dividend_str):
        return "0", dividend_str
    if len(divisor_str) == len(dividend_str):
        if divisor_str > dividend_str:
            return "0", dividend_str
        elif divisor_str == dividend_str:
            return "1", "0"

    # 逐位计算
    divisor_int = int(divisor_str)
    remainder = 0
    quotient_parts = []

    for digit_char in dividend_str:
        remainder = remainder * 10 + int(digit_char)
        q = remainder // divisor_int
        quotient_parts.append(str(q))
        remainder = remainder % divisor_int

    # 清理前导零
    quotient = "".join(quotient_parts).lstrip('0')
    if not quotient:
        quotient = "0"

    return quotient, str(remainder)


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 大整数除法测试 ===\n")

    # 测试基本整数除法
    test_cases = [
        (100, 7),
        (1000, 3),
        (123456, 789),
        (987654321, 12345),
        (2**31, 2**16),
    ]

    print("基本整数除法:")
    for a, b in test_cases:
        q, r = divide_large_int(a, b)
        print(f"  {a} / {b} = {q} ... {r}")
        assert a == b * q + r, "除法验证失败"

    print("\n字符串除法:")
    string_tests = [
        ("12345", "23"),
        ("987654321", "12345"),
        ("1000000", "997"),
    ]

    for dividend, divisor in string_tests:
        q, r = string_division(dividend, divisor)
        print(f"  '{dividend}' / '{divisor}' = '{q}' ... '{r}'")

    print("\n二进制除法:")
    binary_tests = [
        (100, 7),
        (255, 15),
        (1000, 37),
    ]

    for dividend, divisor in binary_tests:
        q, r = binary_division(dividend, divisor)
        print(f"  {dividend} / {divisor} = {q} ... {r}")
        assert dividend == divisor * q + r, "二进制除法验证失败"

    print("\n长除法:")
    long_tests = [
        ("123456789", "1234"),
        ("999999999", "999"),
    ]

    for dividend, divisor in long_tests:
        q, r = long_division(dividend, divisor)
        print(f"  '{dividend}' / '{divisor}' = '{q}' ... '{r}'")
