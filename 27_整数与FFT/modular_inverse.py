# -*- coding: utf-8 -*-
"""
算法实现：27_整数与FFT / modular_inverse

本文件实现 modular_inverse 相关的算法功能。
"""

# =============================================================================
# 扩展欧几里得算法 - Extended Euclidean Algorithm
# =============================================================================

def extended_gcd(a, b):
    """
    扩展欧几里得算法。

    求解：a*x + b*y = gcd(a, b) = d
    当gcd(a,b)=1时，x即为a的模b逆元。

    参数：
        a, b: 两个整数

    返回：
        tuple: (gcd, x, y) 满足 a*x + b*y = gcd
    """
    # 处理边界情况
    if a == 0:
        return b, 0, 1  # gcd(b, 0) = b, x=0, y=1 满足 b*0 + 0*1 = b

    if b == 0:
        return a, 1, 0  # gcd(a, 0) = a, x=1, y=0 满足 a*1 + 0*0 = a

    # 递归计算
    gcd_val, x1, y1 = extended_gcd(b, a % b)

    # 回溯推导
    x = y1
    y = x1 - (a // b) * y1

    return gcd_val, x, y


def modular_inverse_extended_gcd(a, m):
    """
    使用扩展欧几里得算法计算模逆元。

    求解 a^{-1} mod m，使得 a * x ≡ 1 (mod m)

    参数：
        a: 要计算逆元的整数
        m: 模数（正整数）

    返回：
        int: 模逆元 x (0 <= x < m)
        若逆元不存在，返回 -1

    示例：
        modular_inverse_extended_gcd(3, 11) = 4
        因为 3 * 4 = 12 ≡ 1 (mod 11)
    """
    # 确保a在合理范围
    a = a % m
    if a < 0:
        a += m

    gcd_val, x, _ = extended_gcd(a, m)

    # 逆元存在当且仅当gcd(a, m) = 1
    if gcd_val != 1:
        return -1  # 逆元不存在

    # 将x归一化到[0, m-1]
    x = x % m
    if x < 0:
        x += m

    return x


# =============================================================================
# 费马小定理法（仅限素数模）- Fermat's Little Theorem Method
# =============================================================================

def modular_exponentiation(base, exponent, mod):
    """
    快速模幂运算，使用二分平方法。

    计算 base^exponent mod mod

    参数：
        base: 底数
        exponent: 指数（非负整数）
        mod: 模数

    返回：
        int: (base^exponent) mod mod
    """
    if mod == 1:
        return 0

    result = 1
    base = base % mod

    while exponent > 0:
        # 如果指数是奇数，乘以base
        if exponent % 2 == 1:
            result = (result * base) % mod
        # 指数减半
        exponent = exponent // 2
        # base平方
        base = (base * base) % mod

    return result


def modular_inverse_fermat(a, p):
    """
    使用费马小定理计算模逆元（仅当模数为素数时有效）。

    费马小定理：当p为素数时，a^{p-1} ≡ 1 (mod p)
    因此 a * a^{p-2} ≡ 1 (mod p)
    所以 a^{-1} ≡ a^{p-2} (mod p)

    参数：
        a: 底数
        p: 素数模数

    返回：
        int: 模逆元
        若p不是素数或a是p的倍数，结果不正确

    注意：
        此方法需要O(log p)次模乘，比扩展欧几里得慢，
        但当需要计算多个逆元时可以用预计算优化。
    """
    if not is_prime(p):
        raise ValueError(f"模数{p}不是素数，请使用扩展欧几里得算法")

    a = a % p
    if a < 0:
        a += p

    return modular_exponentiation(a, p - 2, p)


# =============================================================================
# 素性检测（辅助函数）- Primality Testing
# =============================================================================

def is_prime(n):
    """
    简单的素性检测（试除法）。

    适用于小到中等规模的数。
    对于大数应使用Miller-Rabin等概率算法。

    参数：
        n: 待检测的整数

    返回：
        bool: True表示是素数
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    if n < 9:
        return True

    # 只需检测到sqrt(n)
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2

    return True


# =============================================================================
# 通用模逆元计算 - Universal Modular Inverse
# =============================================================================

def modular_inverse(a, m, method='auto'):
    """
    统一的模逆元计算接口。

    参数：
        a: 要计算逆元的整数
        m: 模数
        method: 'auto'（自动选择）, 'egcd'（扩展欧几里得）, 'fermat'（费马小定理）

    返回：
        int: 模逆元 x (0 <= x < m)
        若逆元不存在，返回 -1
    """
    if method == 'auto':
        # 自动选择：素数用fermat，否则用egcd
        if is_prime(m):
            return modular_inverse_fermat(a, m)
        else:
            return modular_inverse_extended_gcd(a, m)
    elif method == 'egcd':
        return modular_inverse_extended_gcd(a, m)
    elif method == 'fermat':
        return modular_inverse_fermat(a, m)
    else:
        raise ValueError(f"未知方法: {method}")


# =============================================================================
# 线性同余方程求解 - Linear Congruence Solver
# =============================================================================

def solve_linear_congruence(a, b, m):
    """
    求解线性同余方程：a * x ≡ b (mod m)

    参数：
        a, b, m: 同余方程参数

    返回：
        tuple: (has_solution, x, mod) 若有解返回(True, 一个解, 模数)
              无解返回(False, None, None)

    解的存在条件：
        - 设 d = gcd(a, m)
        - 若 d ∤ b，则无解
        - 若 d | b，则有d个解，周期为m/d

    示例：
        3*x ≡ 5 (mod 7) → x = 4 (因为 3*4=12≡5 mod 7)
    """
    gcd_val, x0, _ = extended_gcd(a, m)

    if b % gcd_val != 0:
        # 无解
        return False, None, None

    # 化简：a' * x ≡ b' (mod m') 其中 a'=a/d, b'=b/d, m'=m/d
    d = gcd_val
    a_prime = a // d
    b_prime = b // d
    m_prime = m // d

    # 求 a' 的逆元（模 m'）
    inv_a_prime = modular_inverse_extended_gcd(a_prime, m_prime)

    # 特解
    x0 = (inv_a_prime * b_prime) % m_prime

    return True, x0, m_prime


# =============================================================================
# 批量模逆元计算 - Batch Modular Inverse
# =============================================================================

def batch_modular_inverse(a_values, m):
    """
    批量计算多个模逆元（在模m下）。

    参数：
        a_values: 整数列表 [a1, a2, ..., an]
        m: 模数

    返回：
        list: 逆元列表 [a1^{-1}, a2^{-1}, ..., an^{-1}]（逆元不存在的位置为-1）

    应用：
        - 密码学批量解密
        - 有限域上的向量运算
        - CRT中的并行计算
    """
    n = len(a_values)
    result = [-1] * n

    for i, a in enumerate(a_values):
        result[i] = modular_inverse_extended_gcd(a, m)

    return result


# =============================================================================
# 应用示例 - Application Examples
# =============================================================================

def demonstrate_crypto_application():
    """
    演示RSA中的模逆元应用。
    RSA密钥生成：
        - 选择两个大素数 p, q
        - 计算 n = p*q, φ(n) = (p-1)*(q-1)
        - 选择公钥指数 e（通常为65537）
        - 计算私钥指数 d = e^{-1} mod φ(n)
    """
    print("=" * 60)
    print("RSA私钥计算中的模逆元应用")
    print("=" * 60)

    # 简化示例（实际中p,q应为大素数）
    p = 61
    q = 53
    n = p * q
    phi_n = (p - 1) * (q - 1)

    # 公钥指数
    e = 17

    # 计算私钥指数 d = e^{-1} mod φ(n)
    d = modular_inverse_extended_gcd(e, phi_n)

    print(f"  p = {p}")
    print(f"  q = {q}")
    print(f"  n = p*q = {n}")
    print(f"  φ(n) = (p-1)*(q-1) = {phi_n}")
    print(f"  公钥指数 e = {e}")
    print(f"  私钥指数 d = e⁻¹ mod φ(n) = {d}")

    # 验证：e * d ≡ 1 (mod φ(n))
    verification = (e * d) % phi_n
    print(f"  验证: e * d mod φ(n) = {e}*{d} mod {phi_n} = {verification}")
    print(f"  {'✓ 正确' if verification == 1 else '✗ 错误'}")


def demonstrate_crt_application():
    """
    演示CRT（中国剩余定理）中的模逆元应用。
    """
    print("\n" + "=" * 60)
    print("中国剩余定理（CRT）中的模逆元")
    print("=" * 60)

    # CRT求解：x ≡ a_i (mod m_i)
    # 关键步骤：计算 M_i = (M/m_i)^{-1} mod m_i

    equations = [
        (2, 3),   # x ≡ 2 (mod 3)
        (3, 5),   # x ≡ 3 (mod 5)
        (2, 7),   # x ≡ 2 (mod 7)
    ]

    # 计算过程
    m_total = 1
    for _, mi in equations:
        m_total *= mi

    print(f"  同余方程组：")
    for ai, mi in equations:
        print(f"    x ≡ {ai} (mod {mi})")

    print(f"  模数乘积 M = {m_total}")

    result = 0
    for ai, mi in equations:
        Mi = m_total // mi
        # 模逆元：Mi^{-1} mod mi
        inv_Mi = modular_inverse_extended_gcd(Mi, mi)
        term = ai * Mi * inv_Mi
        result += term

    result = result % m_total
    print(f"  解：x = {result}")
    print(f"  验证: {result} mod 3 = {result%3}, mod 5 = {result%5}, mod 7 = {result%7}")


# =============================================================================
# 测试 - Tests
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("模逆元计算测试")
    print("=" * 60)

    # 基础测试
    test_cases = [
        (3, 11, 4, "3*4=12≡1 mod 11"),
        (7, 26, 15, "7*15=105≡1 mod 26"),
        (17, 3120, None, "RSA典型值 e=17, φ(n)=3120"),
        (42, 2017, None, "大数模逆"),
    ]

    print("\n基础模逆测试：")
    for a, m, expected, desc in test_cases:
        result = modular_inverse_extended_gcd(a, m)
        if expected is not None:
            status = "✓" if result == expected else "✗"
        else:
            status = "→"
        verification = (a * result) % m
        print(f"  {status} {a}⁻¹ mod {m} = {result} "
              f"(验证: {a}*{result}≡{verification} mod {m}) [{desc}]")

    # 逆元不存在的情况
    print("\n逆元不存在的情况：")
    no_inverse_cases = [(6, 8), (10, 15), (14, 21)]
    for a, m in no_inverse_cases:
        result = modular_inverse_extended_gcd(a, m)
        gcd_val, _, _ = extended_gcd(a, m)
        status = "✓" if result == -1 else "✗"
        print(f"  {status} {a}⁻¹ mod {m} = {result} (gcd({a},{m})={gcd_val})")

    # 线性同余方程求解
    print("\n线性同余方程求解测试：")
    congruence_cases = [
        (3, 5, 7, "3x≡5 mod 7 → x=4"),
        (6, 6, 9, "6x≡6 mod 9 → 解存在"),
        (4, 3, 8, "4x≡3 mod 8 → 无解"),
    ]
    for a, b, m in congruence_cases:
        has_sol, x, new_mod = solve_linear_congruence(a, b, m)
        if has_sol:
            print(f"  ✓ {a}x≡{b} mod {m} → x={x} (mod {new_mod})")
        else:
            print(f"  ✗ {a}x≡{b} mod {m} → 无解")

    # RSA应用
    demonstrate_crypto_application()

    # CRT应用
    demonstrate_crt_application()
