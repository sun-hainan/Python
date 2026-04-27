# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / extended_euclidean

本文件实现 extended_euclidean 相关的算法功能。
"""

def extended_euclidean(a: int, b: int) -> tuple:
    """
    扩展欧几里得算法
    
    计算整数a和b的最大公约数，同时找出贝祖等式 ax + by = gcd(a,b) 的系数
    
    Args:
        a: 第一个整数
        b: 第二个整数
    
    Returns:
        (gcd, x, y) 元组，其中 gcd = ax + by
    """
    if a == 0:
        return b, 0, 1
    if b == 0:
        return a, 1, 0
    
    gcd_val, x1, y1 = extended_euclidean(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    
    return gcd_val, x, y

def modular_inverse(e: int, phi: int) -> int:
    """
    模逆元计算
    
    找到整数x使得 (e * x) % phi = 1
    
    Args:
        e: 需要求逆的数
        phi: 模数
    
    Returns:
        e关于phi的模逆元，如果不存在返回-1
    """
    gcd_val, x, _ = extended_euclidean(e, phi)
    if gcd_val != 1:
        return -1
    return x % phi

if __name__ == "__main__":
    print("=== 扩展欧几里得算法测试 ===")
    test_cases = [(35, 15), (120, 23), (179, 37)]
    
    for a, b in test_cases:
        g, x, y = extended_euclidean(a, b)
        print(f"a={a}, b={b}: gcd={g}, x={x}, y={y}")
        print(f"    验证: {a}*{x} + {b}*{y} = {a*x + b*y}")
    
    print("\n=== 模逆元测试 ===")
    e = 65537
    phi_values = [3120, 4680, 6000]
    for phi in phi_values:
        inv = modular_inverse(e, phi)
        if inv != -1:
            print(f"e={e} 关于 phi={phi} 的逆元: {inv}")
            print(f"    验证: ({e} * {inv}) % {phi} = {(e * inv) % phi}")
