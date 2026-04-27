# -*- coding: utf-8 -*-
"""
算法实现：27_整数与FFT / big_integer

本文件实现 big_integer 相关的算法功能。
"""

import random  # 导入random用于测试数据生成


# =============================================================================
# 数据结构与转换 - Data Structure & Conversion
# =============================================================================

class BigInteger:
    """
    大整数类，使用小端序列表存储十进制位。

    属性：
        digits: list[int], 十进制位列表，最低位在前
               例如：12345 存储为 [5, 4, 3, 2, 1]
        sign: bool, 正负号（True=正，False=负）

    特点：
        - 小端序：便于低位运算（加法、乘法）
        - 每位十进制：0-9，易于人类理解
        - 符号分离：简化运算逻辑
    """

    def __init__(self, value=0, digits=None, sign=True):
        """
        初始化大整数。

        参数：
            value: int 或 str, 初始值（支持负数）
            digits: list[int], 可选，直接提供digit列表
            sign: bool, 符号（仅在digits非空时有效）
        """
        if digits is not None:
            # 直接从digit列表构造
            self.digits = digits[:]  # 复制
            self.sign = sign
            # 去除前导零
            self._normalize()
        else:
            # 从整数或字符串构造
            if isinstance(value, str):
                # 解析字符串
                value = value.strip()
                if value.startswith('-'):
                    self.sign = False
                    value = value[1:]
                else:
                    self.sign = True

                # 解析数字部分
                self.digits = []
                for ch in reversed(value):
                    if ch.isdigit():
                        self.digits.append(int(ch))
                    elif ch == ' ':
                        continue  # 忽略空格
                    else:
                        raise ValueError(f"非法字符: {ch}")

                self._normalize()
            elif isinstance(value, int):
                # 从整数构造
                if value < 0:
                    self.sign = False
                    value = -value
                else:
                    self.sign = True

                if value == 0:
                    self.digits = [0]
                else:
                    self.digits = []
                    while value > 0:
                        self.digits.append(value % 10)
                        value //= 10
            else:
                raise TypeError(f"不支持的类型: {type(value)}")

    def _normalize(self):
        """
        规范化表示：去除前导零。

        例如：[0, 0, 1] → [1]
              [0] → [0]（零保持为[0]）
        """
        while len(self.digits) > 1 and self.digits[-1] == 0:
            self.digits.pop()

    # -------------------------------------------------------------------------
    # 基础属性
    # -------------------------------------------------------------------------

    def is_zero(self):
        """
        判断是否为零。

        返回：
            bool: True表示值为零
        """
        return len(self.digits) == 1 and self.digits[0] == 0

    def is_negative(self):
        """
        判断是否为负数。

        返回：
            bool: True表示为负
        """
        return not self.sign

    def __len__(self):
        """
        返回数字位数（不含符号）。

        返回：
            int: 十进制位数
        """
        return len(self.digits)

    def __repr__(self):
        """
        返回字符串表示。

        返回：
            str: 可打印的字符串
        """
        if self.is_zero():
            return "0"

        sign_str = "-" if not self.sign else ""
        digits_str = "".join(str(d) for d in reversed(self.digits))

        return sign_str + digits_str


# =============================================================================
# 辅助函数 - Helper Functions
# =============================================================================

def ensure_same_length(digits_a, digits_b):
    """
    补齐两个digit列表到相同长度（前面补零）。

    参数：
        digits_a: 第一个digit列表
        digits_b: 第二个digit列表

    返回：
        tuple: (padded_a, padded_b, max_len)
    """
    max_len = max(len(digits_a), len(digits_b))
    a = digits_a + [0] * (max_len - len(digits_a))
    b = digits_b + [0] * (max_len - len(digits_b))
    return a, b, max_len


def strip_leading_zeros(digits):
    """
    去除digit列表的前导零。

    参数：
        digits: digit列表

    返回：
        list: 去除前导零后的列表
    """
    result = digits[:]
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return result


# =============================================================================
# 大整数加法 - Big Integer Addition
# =============================================================================

def big_add(a, b):
    """
    大整数加法（支持正负数）。

    算法：
        从低位到高位逐位相加，记录进位。
        时间复杂度：O(n)

    参数：
        a: BigInteger, 第一个数
        b: BigInteger, 第二个数

    返回：
        BigInteger: a + b
    """
    # 处理特殊情况：零
    if a.is_zero():
        return BigInteger(digits=b.digits[:], sign=b.sign)
    if b.is_zero():
        return BigInteger(digits=a.digits[:], sign=a.sign)

    # 同号：绝对值相加
    if a.sign == b.sign:
        result_sign = a.sign
        result_digits = _add_digits(a.digits, b.digits)
    else:
        # 异号：绝对值相减
        cmp = _compare_abs(a.digits, b.digits)
        if cmp == 0:
            # 互为相反数，结果为零
            return BigInteger(0)
        elif cmp > 0:
            # |a| > |b|，结果为 |a| - |b|
            result_sign = a.sign
            result_digits = _sub_digits(a.digits, b.digits)
        else:
            # |b| > |a|，结果为 |b| - |a|
            result_sign = b.sign
            result_digits = _sub_digits(b.digits, a.digits)

    return BigInteger(digits=result_digits, sign=result_sign)


def _add_digits(digits_a, digits_b):
    """
    两个正整数digit列表相加（无符号）。

    参数：
        digits_a: 第一个数的digit列表（小端序）
        digits_b: 第二个数的digit列表（小端序）

    返回：
        list: 结果的digit列表
    """
    # 补齐长度
    a, b, max_len = ensure_same_length(digits_a, digits_b)

    result = []  # 存储结果
    carry = 0    # 进位

    # 逐位相加
    for i in range(max_len):
        # 当前位求和 + 进位
        total = a[i] + b[i] + carry

        # 记录当前位结果（0-9）
        result.append(total % 10)

        # 计算进位
        carry = total // 10

    # 处理最高位进位
    if carry > 0:
        result.append(carry)

    return result


# =============================================================================
# 大整数减法 - Big Integer Subtraction
# =============================================================================

def big_sub(a, b):
    """
    大整数减法（支持正负数）。

    规则：a - b = a + (-b)
    时间复杂度：O(n)

    参数：
        a: BigInteger, 被减数
        b: BigInteger, 减数

    返回：
        BigInteger: a - b
    """
    # 减法转加法：a - b = a + (-b)
    neg_b = BigInteger(digits=b.digits[:], sign=not b.sign)
    return big_add(a, neg_b)


def _sub_digits(digits_a, digits_b):
    """
    两个正整数digit列表相减，假设 |a| >= |b|。

    算法：
        从低位到高位逐位相减，记录借位。
        时间复杂度：O(n)

    参数：
        digits_a: 被减数的digit列表（假设 |a| >= |b|）
        digits_b: 减数的digit列表

    返回：
        list: 结果的digit列表（正数）
    """
    # 补齐长度
    a, b, max_len = ensure_same_length(digits_a, digits_b)

    result = []  # 存储结果
    borrow = 0   # 借位

    # 逐位相减
    for i in range(max_len):
        # 当前位差 = a[i] - b[i] - 借位
        diff = a[i] - b[i] - borrow

        if diff >= 0:
            # 无需借位
            result.append(diff)
            borrow = 0
        else:
            # 需要借位（借10）
            result.append(diff + 10)
            borrow = 1

    # 去除前导零
    return strip_leading_zeros(result)


def _compare_abs(digits_a, digits_b):
    """
    比较两个正整数的绝对值大小。

    参数：
        digits_a: 第一个数的digit列表
        digits_b: 第二个数的digit列表

    返回：
        int: 1如果 |a| > |b|，0如果相等，-1如果 |a| < |b|
    """
    # 长度比较（长的大）
    if len(digits_a) > len(digits_b):
        return 1
    if len(digits_a) < len(digits_b):
        return -1

    # 长度相同，逐位比较（从高位开始）
    for i in range(len(digits_a) - 1, -1, -1):
        if digits_a[i] > digits_b[i]:
            return 1
        elif digits_a[i] < digits_b[i]:
            return -1

    return 0  # 相等


# =============================================================================
# 大整数乘法 - Big Integer Multiplication
# =============================================================================

def big_mul(a, b):
    """
    大整数乘法（支持正负数）。

    算法：竖式乘法（Schoolbook）
        - 时间复杂度：O(n²)
        - 空间复杂度：O(n)

    原理：
        c[i+j] += a[i] * b[j]，对所有i,j

    参数：
        a: BigInteger, 第一个数
        b: BigInteger, 第二个数

    返回：
        BigInteger: a × b
    """
    # 处理零
    if a.is_zero() or b.is_zero():
        return BigInteger(0)

    # 确定符号
    result_sign = a.sign == b.sign

    # 计算绝对值乘积
    result_digits = _mul_digits(a.digits, b.digits)

    return BigInteger(digits=result_digits, sign=result_sign)


def _mul_digits(digits_a, digits_b):
    """
    两个正整数digit列表相乘（无符号）。

    竖式乘法算法：
        1. 初始化结果数组，长度为 len(a) + len(b)
        2. 对每一对 (i, j)，累加 a[i] * b[j] 到 result[i + j]
        3. 处理进位

    参数：
        digits_a: 第一个数的digit列表
        digits_b: 第二个数的digit列表

    返回：
        list: 乘积的digit列表
    """
    n = len(digits_a)
    m = len(digits_b)

    # 初始化结果数组（最多 n + m 位）
    result = [0] * (n + m)

    # 逐位相乘并累加
    for i in range(n):
        for j in range(m):
            # a[i] * b[j] 累加到 result[i + j]
            result[i + j] += digits_a[i] * digits_b[j]

    # 处理进位
    carry = 0
    for i in range(len(result)):
        total = result[i] + carry
        result[i] = total % 10
        carry = total // 10

    # 去除前导零
    return strip_leading_zeros(result)


# =============================================================================
# 字符串转换与输入 - String Conversion & Input
# =============================================================================

def big_from_string(s):
    """
    从字符串创建BigInteger。

    参数：
        s: str, 数字字符串（可包含负号和空格）

    返回：
        BigInteger: 对应的大整数
    """
    return BigInteger(s)


def big_to_string(a):
    """
    将BigInteger转换为字符串。

    参数：
        a: BigInteger

    返回：
        str: 十进制字符串
    """
    return repr(a)


# =============================================================================
# 比较运算 - Comparison Operations
# =============================================================================

def big_compare(a, b):
    """
    比较两个大整数的大小。

    参数：
        a: BigInteger
        b: BigInteger

    返回：
        int: 1如果 a > b，0如果相等，-1如果 a < b
    """
    # 符号不同
    if a.sign != b.sign:
        return 1 if a.sign else -1

    # 同号：比较绝对值
    cmp = _compare_abs(a.digits, b.digits)

    # 根据符号调整结果
    return cmp if a.sign else -cmp


# =============================================================================
# 幂运算 - Power Operation
# =============================================================================

def big_pow(base, exponent):
    """
    大整数幂运算：base ** exponent。

    使用快速幂（二进制指数）算法：
        - 时间复杂度：O(log exponent × n²)

    参数：
        base: BigInteger, 底数
        exponent: int, 指数（>= 0）

    返回：
        BigInteger: base ** exponent
    """
    if exponent < 0:
        raise ValueError("指数必须为非负整数")

    if exponent == 0:
        return BigInteger(1)

    if exponent == 1:
        return BigInteger(digits=base.digits[:], sign=base.sign)

    # 快速幂：二分
    if exponent % 2 == 0:
        half = big_pow(base, exponent // 2)
        return big_mul(half, half)
    else:
        half = big_pow(base, exponent // 2)
        return big_mul(big_mul(half, half), base)


# =============================================================================
# 主程序测试 - Main Test
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("高精度大整数运算测试")
    print("=" * 60)

    # 1. 基本构造测试
    print("\n[1] 基本构造测试")
    print("-" * 40)

    test_cases = [
        "0",
        "12345",
        "-9876543210",
        "  123 456 ",
        "1000000000000"
    ]

    for s in test_cases:
        try:
            bi = BigInteger(s)
            print(f"  BigInteger('{s}') = {bi}")
        except Exception as e:
            print(f"  BigInteger('{s}') 失败: {e}")

    # 2. 加法测试
    print("\n[2] 加法测试")
    print("-" * 40)

    add_tests = [
        ("12345", "6789"),
        ("99999", "1"),
        ("-123", "456"),
        ("-100", "-200"),
        ("0", "12345"),
    ]

    for a_str, b_str in add_tests:
        a = BigInteger(a_str)
        b = BigInteger(b_str)
        result = big_add(a, b)
        expected = int(a_str) + int(b_str)
        status = "✅" if str(result) == str(expected) else f"❌ (期望{expected})"
        print(f"  {a_str} + {b_str} = {result} {status}")

    # 3. 减法测试
    print("\n[3] 减法测试")
    print("-" * 40)

    sub_tests = [
        ("10000", "1"),
        ("12345", "6789"),
        ("-100", "50"),
        ("-50", "-100"),
        ("0", "0"),
    ]

    for a_str, b_str in sub_tests:
        a = BigInteger(a_str)
        b = BigInteger(b_str)
        result = big_sub(a, b)
        expected = int(a_str) - int(b_str)
        status = "✅" if str(result) == str(expected) else f"❌ (期望{expected})"
        print(f"  {a_str} - {b_str} = {result} {status}")

    # 4. 乘法测试
    print("\n[4] 乘法测试")
    print("-" * 40)

    mul_tests = [
        ("123", "456"),
        ("9999", "9999"),
        ("-123", "45"),
        ("0", "987654321"),
        ("123456789", "987654321"),
    ]

    for a_str, b_str in mul_tests:
        a = BigInteger(a_str)
        b = BigInteger(b_str)
        result = big_mul(a, b)
        expected = int(a_str) * int(b_str)
        status = "✅" if str(result) == str(expected) else f"❌ (期望{expected})"
        print(f"  {a_str} × {b_str} = {result} {status}")

    # 5. 幂运算测试
    print("\n[5] 幂运算测试")
    print("-" * 40)

    pow_tests = [
        ("2", 10),
        ("10", 5),
        ("3", 20),
        ("-2", 5),
    ]

    for base_str, exp in pow_tests:
        base = BigInteger(base_str)
        result = big_pow(base, exp)
        expected = int(base_str) ** exp
        status = "✅" if str(result) == str(expected) else f"❌ (期望{expected})"
        print(f"  {base_str}^{exp} = {result} {status}")

    # 6. 性能测试：大数运算
    print("\n[6] 性能测试（大数运算）")
    print("-" * 40)

    # 生成两个大数
    random.seed(42)
    a_val = random.randint(10**50, 10**51 - 1)
    b_val = random.randint(10**50, 10**51 - 1)

    a = BigInteger(str(a_val))
    b = BigInteger(str(b_val))

    print(f"  a = {str(a)[:20]}... (共{len(a)}位)")
    print(f"  b = {str(b)[:20]}... (共{len(b)}位)")

    import time
    start = time.time()
    sum_result = big_add(a, b)
    add_time = time.time() - start
    print(f"  a + b 计算时间: {add_time*1000:.2f}ms")
    print(f"  结果: {str(sum_result)[:30]}...")

    start = time.time()
    prod_result = big_mul(a, b)
    mul_time = time.time() - start
    print(f"  a × b 计算时间: {mul_time*1000:.2f}ms")
    print(f"  结果: {str(prod_result)[:30]}...")

    # 验证
    expected_sum = a_val + b_val
    expected_prod = a_val * b_val
    print(f"\n  验证加法: {'✅ 正确' if str(sum_result) == str(expected_sum) else '❌ 错误'}")
    print(f"  验证乘法: {'✅ 正确' if str(prod_result) == str(expected_prod) else '❌ 错误'}")

    # 7. 比较运算测试
    print("\n[7] 比较运算测试")
    print("-" * 40)

    compare_tests = [
        ("100", "99"),
        ("-100", "-99"),
        ("12345", "12345"),
        ("999", "1000"),
    ]

    for a_str, b_str in compare_tests:
        a = BigInteger(a_str)
        b = BigInteger(b_str)
        cmp = big_compare(a, b)
        expected_cmp = 1 if int(a_str) > int(b_str) else (-1 if int(a_str) < int(b_str) else 0)
        status = "✅" if cmp == expected_cmp else f"❌ (期望{expected_cmp})"
        result_str = ">" if cmp == 1 else ("<" if cmp == -1 else "==")
        print(f"  {a_str} {result_str} {b_str} {status}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
