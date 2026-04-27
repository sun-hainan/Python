# -*- coding: utf-8 -*-

"""

算法实现：27_整数与FFT / karatsuba_multiplication



本文件实现 karatsuba_multiplication 相关的算法功能。

"""



import math

from typing import List





def get_bit_length(n: int) -> int:

    """获取整数的二进制位数"""

    if n == 0:

        return 1

    return n.bit_length()





def karatsuba_multiply(x: int, y: int) -> int:

    """

    Karatsuba 大整数乘法

    

    参数:

        x: 第一个整数

        y: 第二个整数

    

    返回:

        x * y 的乘积

    

    复杂度: T(n) = 3*T(n/2) + O(n), 解为 O(n^log2(3))

    """

    # 基础情况: 小于 2 位数字直接相乘

    if x < 10 or y < 10:

        return x * y

    

    # 计算两个数中较长的位数, 并向上取整到偶数

    n = max(get_bit_length(x), get_bit_length(y))

    m = (n + 1) // 2  # 分割点, 基数约为 2^m

    

    # 计算基数 B = 2^m

    base = 1 << m

    

    # 分解 x = x1 * base + x0

    x1 = x >> m

    x0 = x & (base - 1)

    

    # 分解 y = y1 * base + y0

    y1 = y >> m

    y0 = y & (base - 1)

    

    # 递归计算三个乘法

    z0 = karatsuba_multiply(x0, y0)       # a0 * b0

    z2 = karatsuba_multiply(x1, y1)       # a1 * b1

    z1 = karatsuba_multiply(x1 + x0, y1 + y0) - z2 - z0  # (a1+a0)*(b1+b0) - a1*b1 - a0*b0

    

    # 合并结果: a*b = z2 * base² + z1 * base + z0

    return z2 * (base << m) + z1 * base + z0





def karatsuba_multiply_list(a: List[int], b: List[int]) -> List[int]:

    """

    基于数组表示的大整数 Karatsuba 乘法

    

    参数:

        a: 第一个数, 低位在前, 每位为 0-9 或更大基数

        b: 第二个数, 低位在前

    

    返回:

        乘积结果, 低位在前

    

    示例:

        a = [3, 2, 1] 表示 123

        b = [4, 5] 表示 54

        结果为 123 * 54 = 6642 表示为 [2, 4, 6, 6]

    """

    if len(a) <= 4 or len(b) <= 4:

        # 基础情况: 使用简单乘法

        result = [0] * (len(a) + len(b))

        for i, ai in enumerate(a):

            carry = 0

            for j, bj in enumerate(b):

                result[i + j] += ai * bj + carry

                carry = result[i + j] // 10

                result[i + j] %= 10

            if carry > 0:

                result[i + len(b)] = carry

        # 去除前导零

        while len(result) > 1 and result[-1] == 0:

            result.pop()

        return result

    

    # 找到较长的长度, 分割

    n = max(len(a), len(b))

    m = (n + 1) // 2

    

    # 分割 a 和 b

    a0 = a[:m]

    a1 = a[m:] if len(a) > m else [0]

    b0 = b[:m]

    b1 = b[m:] if len(b) > m else [0]

    

    # 递归计算三个乘法

    z0 = karatsuba_multiply_list(a0, b0)      # a0 * b0

    z2 = karatsuba_multiply_list(a1, b1)      # a1 * b1

    a1_plus_a0 = add_list(a1, a0)             # a1 + a0

    b1_plus_b0 = add_list(b1, b0)             # b1 + b0

    z1_mixed = karatsuba_multiply_list(a1_plus_a0, b1_plus_b0)

    z1 = subtract_list(subtract_list(z1_mixed, z2), z0)  # (a1+a0)*(b1+b0) - a1*b1 - a0*b0

    

    # 合并结果: z2 * base^(2m) + z1 * base^m + z0

    # z2 左移 2*m 位, z1 左移 m 位

    temp1 = shift_list(z2, 2 * m)

    temp2 = shift_list(z1, m)

    

    result = add_list(add_list(temp1, temp2), z0)

    return result





def add_list(a: List[int], b: List[int]) -> List[int]:

    """列表表示的大整数加法, 低位在前"""

    n = max(len(a), len(b))

    result = []

    carry = 0

    for i in range(n):

        ai = a[i] if i < len(a) else 0

        bi = b[i] if i < len(b) else 0

        total = ai + bi + carry

        result.append(total % 10)

        carry = total // 10

    if carry > 0:

        result.append(carry)

    return result





def subtract_list(a: List[int], b: List[int]) -> List[int]:

    """列表表示的大整数减法 (假设 a >= b), 低位在前"""

    result = []

    borrow = 0

    for i in range(len(a)):

        ai = a[i]

        bi = b[i] if i < len(b) else 0

        diff = ai - bi - borrow

        if diff < 0:

            diff += 10

            borrow = 1

        else:

            borrow = 0

        result.append(diff)

    # 去除前导零

    while len(result) > 1 and result[-1] == 0:

        result.pop()

    return result





def shift_list(a: List[int], k: int) -> List[int]:

    """将列表表示的数左移 k 位 (乘以 base^k)"""

    return [0] * k + a





def list_to_int(a: List[int]) -> int:

    """将列表转换为 Python int"""

    result = 0

    for digit in reversed(a):

        result = result * 10 + digit

    return result





def int_to_list(n: int) -> List[int]:

    """将 Python int 转换为列表 (低位在前)"""

    if n == 0:

        return [0]

    result = []

    while n > 0:

        result.append(n % 10)

        n //= 10

    return result





# ============================================================

# 测试代码

# ============================================================



if __name__ == "__main__":

    print("=" * 60)

    print("Karatsuba 乘法测试")

    print("=" * 60)

    

    # 测试 1: 基本乘法验证

    test_cases = [

        (1234, 5678),

        (123456789, 987654321),

        (999999999, 123456789),

        (1 << 100, 1 << 50),  # 大数测试

        (12345678901234567890, 98765432109876543210),

    ]

    

    print("\n--- int 乘法测试 (Karatsuba vs Python 内置) ---")

    for x, y in test_cases:

        result = karatsuba_multiply(x, y)

        expected = x * y

        status = "✓" if result == expected else "✗"

        print(f"{status} karatsuba({x}, {y}) = {result}")

        print(f"   内置乘法: {x * y}, 匹配: {result == expected}")

        print()

    

    # 测试 2: 列表乘法测试

    print("--- 列表表示乘法测试 ---")

    list_test_cases = [

        ([3, 2, 1], [4, 5]),           # 123 * 54 = 6642

        ([9, 9, 9], [1]),              # 999 * 1 = 999

        ([1, 0, 0], [1, 0, 0]),       # 001 * 001 = 1

    ]

    

    for a, b in list_test_cases:

        result = karatsuba_multiply_list(a, b)

        expected_int = list_to_int(a) * list_to_int(b)

        result_int = list_to_int(result)

        status = "✓" if result_int == expected_int else "✗"

        print(f"{status} {a} * {b} = {result} (期望: {expected_int}, 实际: {result_int})")

    

    # 测试 3: 性能对比

    print("\n--- 性能对比 (大数) ---")

    import time

    

    large_x = (1 << 1000) - 1   # 约 300 位十进制数

    large_y = (1 << 500) - 1

    

    start = time.time()

    for _ in range(100):

        _ = karatsuba_multiply(large_x, large_y)

    karatsuba_time = time.time() - start

    

    start = time.time()

    for _ in range(100):

        _ = large_x * large_y

    builtin_time = time.time() - start

    

    print(f"Karatsuba (100次): {karatsuba_time:.4f}s")

    print(f"Python内置 (100次): {builtin_time:.4f}s")

    print(f"Python 内置在大数场景更快 (CPython 已用 Karatsuba/FFT 优化)")

    

    # 测试 4: 复杂度验证

    print("\n--- 复杂度验证 (Karatsuba 递归深度) ---")

    def count_recursion_depth(x: int, y: int, depth: int = 0) -> int:

        """计算递归最大深度"""

        if x < 10 or y < 10:

            return depth

        n = max(get_bit_length(x), get_bit_length(y))

        m = (n + 1) // 2

        base = 1 << m

        x1, x0 = x >> m, x & (base - 1)

        y1, y0 = y >> m, y & (base - 1)

        return max(

            count_recursion_depth(x0, y0, depth + 1),

            count_recursion_depth(x1, y1, depth + 1),

            count_recursion_depth(x1 + x0, y1 + y0, depth + 1)

        )

    

    for n in [10, 50, 100, 200]:

        x = (1 << n) - 1  # n 位的全 1

        y = 1

        depth = count_recursion_depth(x, y)

        print(f"  {n} 位数最大递归深度: {depth} (理论 log2({n}) ≈ {n/2:.1f})")

    

    print("\n" + "=" * 60)

    print("Karatsuba 算法总结:")

    print("- 时间复杂度: O(n^log2(3)) ≈ O(n^1.585)")

    print("- 空间复杂度: O(n) (递归栈)")

    print("- 核心技巧: 将 4 次乘法减少到 3 次")

    print("- 限制: 递归调用开销大, Python 内置已更优化")

    print("=" * 60)

