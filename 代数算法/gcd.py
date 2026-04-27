# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / gcd

本文件实现 gcd 相关的算法功能。
"""

def gcd(a: int, b: int) -> int:
    """
    最大公约数 - 欧几里得算法（迭代版本）
    
    Args:
        a: 第一个整数
        b: 第二个整数
    
    Returns:
        a和b的最大公约数
    """
    while b != 0:
        a, b = b, a % b
    return abs(a)

def gcd_recursive(a: int, b: int) -> int:
    """
    最大公约数 - 欧几里得算法（递归版本）
    
    Args:
        a: 第一个整数
        b: 第二个整数
    
    Returns:
        a和b的最大公约数
    """
    if b == 0:
        return abs(a)
    return gcd_recursive(b, a % b)

def lcm(a: int, b: int) -> int:
    """最小公倍数"""
    return abs(a * b) // gcd(a, b)

if __name__ == "__main__":
    test_pairs = [(48, 18), (100, 35), (17, 13), (24, 16)]
    
    print("=== 欧几里得算法测试 ===")
    for a, b in test_pairs:
        result = gcd(a, b)
        result_rec = gcd_recursive(a, b)
        print(f"GCD({a}, {b}) = {result} (迭代) = {result_rec} (递归)")
    
    print("\n=== 最小公倍数测试 ===")
    for a, b in test_pairs:
        result_lcm = lcm(a, b)
        print(f"LCM({a}, {b}) = {result_lcm}")
    
    print("\n=== 验证 ===")
    for a, b in test_pairs:
        g = gcd(a, b)
        print(f"{a}*{b} = {a*b}, {g}*{lcm(a,b)} = {g*lcm(a,b)}, 一致={a*b == g*lcm(a,b)}")
