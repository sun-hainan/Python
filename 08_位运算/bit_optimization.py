# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / bit_optimization

本文件实现 bit_optimization 相关的算法功能。
"""

def multiply_power_of_two(a: int, n: int) -> int:
    """乘以2^n：左移n位"""
    return a << n

def divide_power_of_two(a: int, n: int) -> int:
    """除以2^n：右移n位（向下取整）"""
    return a >> n

def modulo_power_of_two(a: int, n: int) -> int:
    """对2^n取模：a & (2^n - 1) == a % 2^n"""
    return a & ((1 << n) - 1)

def is_divisible_by_power_of_two(a: int, n: int) -> bool:
    """判断a是否能被2^n整除：a & (2^n - 1) == 0"""
    return (a & ((1 << n) - 1)) == 0

def average_two(a: int, b: int) -> int:
    """两数平均：(a + b) // 2，避免溢出 -> (a | b) + (a & b) >> 1"""
    return (a + b) >> 1

def average_safe(a: int, b: int) -> int:
    """安全平均（防止溢出）"""
    return (a | b) + ((a ^ b) >> 1)

def round_up_to_power_of_two(n: int) -> int:
    """向上取整到最近的2的幂次"""
    if n == 0:
        return 1
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    return n + 1

def floor_to_power_of_two(n: int) -> int:
    """向下取整到2的幂次"""
    return 1 << (n.bit_length() - 1)

def multiply_by_3_divisible_check(n: int) -> bool:
    """检测n*3是否溢出或被3整除（n*3 = (n<<1) + n）"""
    return ((n << 1) + n) % 3 == 0

def abs_without_branch(x: int) -> int:
    """无分支求绝对值（利用符号位）"""
    mask = x >> 31  # 全0或全1（符号位扩展）
    return (x + mask) ^ mask  # x + mask后符号位翻转，再XOR mask

def clamp(value: int, lo: int, hi: int) -> int:
    """无分支限幅"""
    return max(lo, min(hi, value))

def is_alternating_bits(n: int) -> bool:
    """检测n是否为01交替模式（101010...）：n ^ (n >> 1) 为全1"""
    return (n ^ (n >> 1)) == ((1 << n.bit_length()) - 1)


if __name__ == "__main__":
    import time

    # 速度对比测试
    size = 10_000_000
    vals = list(range(size))

    start = time.perf_counter()
    _ = [v % 1024 for v in vals]
    t_mod = time.perf_counter() - start

    start = time.perf_counter()
    _ = [v & 1023 for v in vals]
    t_bit = time.perf_counter() - start

    print(f"取模运算耗时: {t_mod:.4f}s")
    print(f"位与运算耗时: {t_bit:.4f}s")
    print(f"加速比: {t_mod/t_bit:.2f}x")

    # 功能演示
    print("\n=== 功能演示 ===")
    print(f"100 * 8 = {multiply_power_of_two(100, 3)}")
    print(f"100 / 4 = {divide_power_of_two(100, 2)}")
    print(f"155 % 16 = {modulo_power_of_two(155, 4)}")
    print(f"128能被16整除? {is_divisible_by_power_of_two(128, 4)}")
    print(f"15向上取整到2的幂: {round_up_to_power_of_two(15)}")
    print(f"23向下取整到2的幂: {floor_to_power_of_two(23)}")
    print(f"-42的绝对值: {abs_without_branch(-42)}")
    print(f"85限幅到[10,50]: {clamp(85, 10, 50)}")
    print(f"170是否为01交替: {is_alternating_bits(170)}")  # 170=10101010
