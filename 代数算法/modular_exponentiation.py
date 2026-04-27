# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / modular_exponentiation

本文件实现 modular_exponentiation 相关的算法功能。
"""

def modular_exponentiation(base: int, exp: int, mod: int) -> int:
    """
    快速模幂运算 - 平方乘算法
    
    高效计算 (base^exp) % mod，避免大数溢出
    
    Args:
        base: 底数
        exp: 指数
        mod: 模数
    
    Returns:
        (base^exp) % mod 的结果
    """
    result = 1
    base = base % mod
    
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        exp = exp // 2
        base = (base * base) % mod
    
    return result

def fermat_prime_test(n: int, k: int = 5) -> bool:
    """
    费马素性测试
    
    Args:
        n: 待检测的数
        k: 测试轮数
    
    Returns:
        如果通过所有测试返回True（可能是素数），否则返回False
    """
    import random
    
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    for _ in range(k):
        a = random.randrange(2, n - 1)
        if modular_exponentiation(a, n - 1, n) != 1:
            return False
    
    return True

if __name__ == "__main__":
    print("=== 快速模幂运算测试 ===")
    result = modular_exponentiation(2, 10, 1000)
    print(f"2^10 mod 1000 = {result} (预期: 24)")
    
    result = modular_exponentiation(3, 5, 13)
    print(f"3^5 mod 13 = {result} (预期: 9)")
    
    result = modular_exponentiation(7, 100, 13)
    print(f"7^100 mod 13 = {result}")
    
    print("\n=== 费马素性测试 ===")
    test_numbers = [17, 561, 97, 100, 13, 1729]
    for n in test_numbers:
        is_prime = fermat_prime_test(n)
        print(f"{n}: {'可能是素数' if is_prime else '是合数'}")
