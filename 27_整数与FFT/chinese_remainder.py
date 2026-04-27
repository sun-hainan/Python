# -*- coding: utf-8 -*-
"""
算法实现：27_整数与FFT / chinese_remainder

本文件实现 chinese_remainder 相关的算法功能。
"""

def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """
    扩展欧几里得算法

    返回：(gcd, x, y) 使得 a*x + b*y = gcd(a, b)
    其中 x 是 a 关于 b 的模逆元（当 gcd=1 时）
    """
    if b == 0:
        return a, 1, 0
    else:
        gcd, x1, y1 = extended_gcd(b, a % b)
        x = y1
        y = x1 - (a // b) * y1
        return gcd, x, y


def mod_inverse(a: int, m: int) -> int:
    """
    求 a 在模 m 下的乘法逆元

    要求：gcd(a, m) = 1

    返回：a^(-1) mod m
    """
    gcd, x, _ = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError(f"{a} 和 {m} 不互质，无法求逆元")
    return x % m


def crt_pair(a1: int, m1: int, a2: int, m2: int) -> tuple[int, int]:
    """
    合并两个同余方程

    x ≡ a1 (mod m1)
    x ≡ a2 (mod m2)

    返回：(x, lcm(m1, m2)) 满足两个方程的最小正整数解

    推导：
        x = a1 + m1*k
        a1 + m1*k ≡ a2 (mod m2)
        m1*k ≡ (a2 - a1) (mod m2)
        k ≡ (a2 - a1) / m1 (mod m2/m1_gcd)

    适用范围：m1 和 m2 不一定互质
    """
    # 计算 g = gcd(m1, m2)
    g = 0
    for i in range(1, min(m1, m2) + 1):
        if m1 % i == 0 and m2 % i == 0:
            g = i

    # 可解性检查：(a2 - a1) 必须能被 g 整除
    if (a2 - a1) % g != 0:
        raise ValueError(f"方程无解：{a1} mod {m1} 和 {a2} mod {m2}")

    # 计算 lcm
    lcm = (m1 // g) * m2

    # 计算 k
    # m1*g^(-1)*k ≡ (a2-a1)/g (mod m2/g)
    m1_div_g = m1 // g
    m2_div_g = m2 // g
    diff = (a2 - a1) // g

    # 求 m1_div_g 在模 m2_div_g 下的逆元
    inv = mod_inverse(m1_div_g % m2_div_g, m2_div_g)
    k = (diff * inv) % m2_div_g

    x = (a1 + m1 * k) % lcm
    return x, lcm


def chinese_remainder_theorem(remainders: list[int], moduli: list[int]) -> int:
    """
    中国剩余定理 - 多个方程

    参数：
        remainders: 余数列表 [a1, a2, ..., ak]
        moduli: 模数列表 [m1, m2, ..., mk]

    返回：满足所有方程的最小正整数 x

    算法：两两合并
    """
    if len(remainders) != len(moduli):
        raise ValueError("余数和模数数量必须相同")

    if len(remainders) == 0:
        return 0

    if len(remainders) == 1:
        return remainders[0] % moduli[0]

    # 两两合并
    x, m = remainders[0], moduli[0]
    for i in range(1, len(remainders)):
        x, m = crt_pair(x, m, remainders[i], moduli[i])

    return x % m


def chinese_remainder_coprime(remainders: list[int], moduli: list[int]) -> int:
    """
    互质情况的中国剩余定理 - 公式法

    假设所有 moduli 互质，效率更高

    x = Σ(ai * Mi * Ti) mod M

    其中：
        M = ∏ mi
        Mi = M / mi
        Ti = Mi^(-1) mod mi
    """
    M = 1
    for m in moduli:
        M *= m

    x = 0
    for i in range(len(remainders)):
        Mi = M // moduli[i]
        Ti = mod_inverse(Mi, moduli[i])
        x = (x + remainders[i] * Mi * Ti) % M

    return x


def solve_congruence(a: int, b: int, m: int) -> list[int]:
    """
    求同余方程 a*x ≡ b (mod m) 的解

    返回：所有满足的 x（取模 m 后的非负代表）
    """
    g = 0
    for i in range(1, min(a, m) + 1):
        if a % i == 0 and m % i == 0:
            g = i

    if b % g != 0:
        return []  # 无解

    # 简化方程
    a1 = a // g
    b1 = b // g
    m1 = m // g

    # 求逆元
    inv = mod_inverse(a1 % m1, m1)
    x0 = (b1 * inv) % m1

    # 所有解：x0 + k*m1, k = 0, 1, ..., g-1
    return [(x0 + k * m1) % m for k in range(g)]


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 中国剩余定理测试 ===\n")

    # 测试1：经典问题 - 孙子算经
    print("【孙子算经】有三数不知其名，分别余3、余5、余7，求此数？")
    x = chinese_remainder_coprime([3, 5, 7], [3, 5, 7])  # 注意：实际应该是 3x≡? 对不同模
    x = chinese_remainder_theorem([2, 3, 2], [3, 5, 7])  # x mod 3 = 2, x mod 5 = 3, x mod 7 = 2
    print(f"  解：x = {x}")
    print(f"  验证：{x} mod 3 = {x % 3} (应为 2)")
    print(f"        {x} mod 5 = {x % 5} (应为 3)")
    print(f"        {x} mod 7 = {x % 7} (应为 2)")

    # 测试2：两两合并
    print("\n【两两合并】")
    x, m = crt_pair(2, 3, 3, 5)
    print(f"  x ≡ 2 (mod 3) 和 x ≡ 3 (mod 5) => x = {x} (mod {m})")

    x, m = crt_pair(x, m, 2, 7)
    print(f"  再加上 x ≡ 2 (mod 7) => x = {x} (mod {m})")

    # 测试3：非互质情况
    print("\n【非互质情况】")
    try:
        x, m = crt_pair(3, 6, 10, 15)
        print(f"  x ≡ 3 (mod 6) 和 x ≡ 10 (mod 15) => x = {x} (mod {m})")
        print(f"  验证：{x} mod 6 = {x % 6}, {x} mod 15 = {x % 15}")
    except ValueError as e:
        print(f"  无解: {e}")

    # 测试4：同余方程求解
    print("\n【同余方程求解】")
    solutions = solve_congruence(14, 30, 100)
    print(f"  14*x ≡ 30 (mod 100) 的解: {solutions}")
    for sol in solutions:
        print(f"    {sol}*14 mod 100 = {(sol*14) % 100}")

    # 测试5：实际应用 - 日期计算
    print("\n【日期计算】")
    print("  今天星期二(2)，10天后星期几？20天后呢？")
    days_10 = (2 + 10) % 7
    days_20 = (2 + 20) % 7
    print(f"    10天后: 星期{['一','二','三','四','五','六','日'][days_10]}")
    print(f"    20天后: 星期{['一','二','三','四','五','六','日'][days_20]}")

    # 测试6：Shor算法辅助
    print("\n【Shor算法辅助】")
    print("  求满足以下条件的最小正整数 x：")
    print("    x ≡ 5 (mod 21)")
    print("    x ≡ 11 (mod 26)")
    print("    x ≡ 3 (mod 5)")
    try:
        x = chinese_remainder_theorem([5, 11, 3], [21, 26, 5])
        print(f"    解：x = {x}")
        print(f"    验证：x mod 21 = {x % 21} (应为 5)")
        print(f"          x mod 26 = {x % 26} (应为 11)")
        print(f"          x mod 5 = {x % 5} (应为 3)")
    except Exception as e:
        print(f"    错误: {e}")
