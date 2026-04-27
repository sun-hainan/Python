# -*- coding: utf-8 -*-
"""
算法实现：27_整数与FFT / crt_application

本文件实现 crt_application 相关的算法功能。
"""

# =============================================================================
# 辅助函数 - Helpers
# =============================================================================

def extended_gcd(a, b):
    """
    扩展欧几里得算法。

    返回 (gcd, x, y) 使得 a*x + b*y = gcd(a, b)
    当gcd=1时，x是a关于b的模逆元。
    """
    if b == 0:
        return a, 1, 0
    gcd_val, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return gcd_val, x, y


def modular_inverse(a, m):
    """
    计算a关于m的模逆元。

    返回 x 使得 a*x ≡ 1 (mod m)
    若不存在返回-1。
    """
    gcd_val, x, _ = extended_gcd(a % m, m)
    if gcd_val != 1:
        return -1
    return x % m


# =============================================================================
# 标准CRT（互质情况）- Standard CRT (Coprime Moduli)
# =============================================================================

def crt_standard(remainders, moduli):
    """
    标准中国剩余定理求解。

    求解同余方程组：
        x ≡ remainders[i] (mod moduli[i])
    其中所有moduli两两互质。

    参数：
        remainders: list[int]，余数列表 [a1, a2, ..., ak]
        moduli: list[int]，模数列表 [m1, m2, ..., mk]

    返回：
        tuple: (solution, M)
            solution: 满足所有同余式的最小非负整数
            M: 模数乘积（解的周期）

    示例：
        x ≡ 2 (mod 3)
        x ≡ 3 (mod 5)
        x ≡ 2 (mod 7)
        → crt_standard([2,3,2], [3,5,7]) = (23, 105)
    """
    if len(remainders) != len(moduli):
        raise ValueError("remainders和moduli长度必须一致")

    # 计算模数乘积 M
    M = 1
    for mi in moduli:
        M *= mi

    # 计算最终解
    x = 0
    for ai, mi in zip(remainders, moduli):
        Mi = M // mi          # M_i = M / m_i
        Ni = modular_inverse(Mi % mi, mi)  # N_i = M_i^{-1} mod m_i
        if Ni == -1:
            raise ValueError(f"模数{mi}与其它模数不互质")
        term = ai * Mi * Ni
        x += term

    # 归一化到 [0, M)
    x = x % M
    return x, M


# =============================================================================
# 扩展CRT（不互质情况）- Extended CRT (Non-coprime Moduli)
# =============================================================================

def crt_extended(remainders, moduli):
    """
    扩展中国剩余定理，支持模数不互质的情况。

    方程组：
        x ≡ remainders[i] (mod moduli[i])

    解的存在条件：
        - 对任意i≠j，有 gcd(moduli[i], moduli[j]) | (remainders[i] - remainders[j])
        - 即相邻模数的最大公约数必须整除相应的余数差

    参数：
        remainders: list[int]，余数列表
        moduli: list[int]，模数列表（不一定互质）

    返回：
        tuple: (has_solution, solution, lcm)
            has_solution: bool，是否有解
            solution: int，最小非负解（若有解）
            lcm: int，所有模数的最小公倍数（解的周期）

    示例：
        x ≡ 2 (mod 4)
        x ≡ 3 (mod 6)
        → gcd(4,6)=2, 3-2=1不能被2整除 → 无解
    """
    if len(remainders) != len(moduli):
        raise ValueError("remainders和moduli长度必须一致")

    # 从第一个方程开始，逐步合并
    r1, m1 = remainders[0], moduli[0]

    for i in range(1, len(remainders)):
        r2, m2 = remainders[i], moduli[i]

        # 合并方程：x ≡ r1 (mod m1) 和 x ≡ r2 (mod m2)
        has_sol, r, d = merge_two_congruences(r1, m1, r2, m2)

        if not has_sol:
            return False, None, None

        # 更新为合并后的方程
        r1 = r        # 新余数
        m1 = d        # 新模数（实际是lcm(m1,m2)）

    # 归一化
    lcm_total = m1
    solution = r1 % lcm_total
    if solution < 0:
        solution += lcm_total

    return True, solution, lcm_total


def merge_two_congruences(r1, m1, r2, m2):
    """
    合并两个同余方程。

    求解：
        x ≡ r1 (mod m1)
        x ≡ r2 (mod m2)

    返回：
        tuple: (has_solution, r_combined, lcm)
    """
    # 计算gcd和lcm
    gcd_val, p, _ = extended_gcd(m1, m2)
    lcm = m1 // gcd_val * m2  # 避免溢出

    # 检查可解性
    diff = r2 - r1
    if diff % gcd_val != 0:
        return False, None, None

    # 计算合并后的解
    # 使用中国剩余定理的构造公式
    # x = r1 + m1 * t，其中 t 满足 m1*t ≡ (r2-r1) (mod m2)
    # 即 t ≡ (r2-r1)/m1 * (m1/gcd)^{-1} (mod m2/gcd)

    m1_div = m1 // gcd_val
    m2_div = m2 // gcd_val
    diff_div = diff // gcd_val

    # 逆元存在（因为m1_div和m2_div互质）
    inv_m1_div = modular_inverse(m1_div % m2_div, m2_div)
    t = (diff_div * inv_m1_div) % m2_div

    r_combined = r1 + m1 * t
    lcm = m1_div * m2  # = lcm(m1, m2)

    # 归一化
    r_combined = r_combined % lcm
    if r_combined < 0:
        r_combined += lcm

    return True, r_combined, lcm


# =============================================================================
# RSA解密加速应用 - RSA Decryption Speedup
# =============================================================================

def rsa_crt_speedup(ciphertext, d, p, q):
    """
    使用CRT加速RSA解密。

    背景：
        RSA解密需要计算 M = C^d mod n
        直接计算需要O(log d)次大数模乘
        使用CRT可以将模数分解为p和q，模乘效率提升约4倍

    算法：
        M_p = C^{d mod (p-1)} mod p  （因为 d_p ≡ d (mod p-1)）
        M_q = C^{d mod (q-1)} mod q
        M = CRT(M_p mod p, M_q mod q) = M_p * q * (q^{-1} mod p) + M_q * p * (p^{-1} mod q) mod n

    参数：
        ciphertext: int，密文
        d: int，私钥指数
        p, q: int，两个大素数

    返回：
        int，明文消息
    """
    n = p * q
    phi_n = (p - 1) * (q - 1)

    # 计算 d mod (p-1) 和 d mod (q-1)
    dp = d % (p - 1)
    dq = d % (q - 1)

    # 计算 q^{-1} mod p 和 p^{-1} mod q
    inv_q_mod_p = modular_inverse(q % p, p)
    inv_p_mod_q = modular_inverse(p % q, q)

    # 分别在p和q下解密
    mp = pow(ciphertext % p, dp, p)  # C^{d_p} mod p
    mq = pow(ciphertext % q, dq, q)  # C^{d_q} mod q

    # CRT合并
    # M = mp * q * q^{-1} + mq * p * p^{-1} (mod n)
    h = (inv_q_mod_p * (mp - mq)) % p
    plaintext = mq + h * q

    return plaintext


# =============================================================================
# 星期几计算应用 - Day of Week Calculation
# =============================================================================

def day_of_week_with_crt(year, month, day):
    """
    使用CRT计算给定日期是星期几。

    原理：
        将星期循环看作模7的同余运算，
        不同月份的天数差异看作不同模数。

    参数：
        year, month, day: 年、月、日

    返回：
        int: 0=星期一, 1=星期二, ..., 6=星期日
    """
    import datetime

    try:
        dt = datetime.date(year, month, day)
        return (dt.weekday() + 1) % 7  # 转换为 0=星期一
    except:
        return None


# =============================================================================
# 大整数模运算应用 - Large Integer Mod Operations
# =============================================================================

def solve_large_mod_system(remainders, moduli, verbose=True):
    """
    求解大型同余方程组。

    应用场景：
        - 将大数表示为多个小模数的余数（类似-split运算）
        - 密码学中的分布式密钥共享
        - 高效的大数运算

    示例：
        x ≡ 1 (mod 2)
        x ≡ 2 (mod 3)
        x ≡ 3 (mod 4)
        x ≡ 4 (mod 5)
        x ≡ 0 (mod 6)
        → x = ?（Shor算法的周期估计相关）
    """
    # 先用扩展CRT尝试
    has_sol, solution, lcm = crt_extended(remainders, moduli)

    if has_sol:
        if verbose:
            print(f"解存在：x ≡ {solution} (mod {lcm})")
        return solution, lcm
    else:
        if verbose:
            print("解不存在：模数不满足可解性条件")
        return None, None


# =============================================================================
# 密码学应用：秘密共享 - Secret Sharing
# =============================================================================

def secret_sharing_crt(secret, shares):
    """
    使用CRT实现简单的秘密共享。

    原理：
        将秘密S编码为同余方程组的唯一解
        每个参与者持有 (m_i, a_i) 其中 a_i ≡ S (mod m_i)
        任意足够多的参与者可以恢复S

    参数：
        secret: int，要分享的秘密
        shares: list[tuple]，分享数据 [(m1,a1), (m2,a2), ...]

    返回：
        int，CRT恢复的秘密值

    示例：
        secret = 42
        shares = [(3, 0), (5, 2), (7, 0)]
        解释：42 mod 3 = 0, 42 mod 5 = 2, 42 mod 7 = 0
    """
    moduli = [m for m, _ in shares]
    remainders = [a for _, a in shares]

    solution, _ = crt_standard(remainders, moduli)
    return solution


# =============================================================================
# 可视化演示 - Visualization Demo
# =============================================================================

def demonstrate_crt_visual():
    """
    可视化CRT的解空间。
    展示在2D网格上，同余方程组的解如何形成网格线交点。
    """
    print("=" * 60)
    print("CRT方程组求解可视化")
    print("=" * 60)

    # 方程组：x ≡ 2 (mod 3), x ≡ 3 (mod 5), x ≡ 2 (mod 7)
    remainders = [2, 3, 2]
    moduli = [3, 5, 7]

    print(f"\n方程组：")
    for i, (a, m) in enumerate(zip(remainders, moduli)):
        print(f"  方程{i+1}: x ≡ {a} (mod {m})")

    solution, M = crt_standard(remainders, moduli)

    print(f"\n解：x = {solution} (mod {M})")
    print(f"\n验证（前10个解）：")
    for k in range(10):
        x = solution + k * M
        checks = " ".join(f"mod{m}= {x%m}" for m in moduli)
        print(f"  x = {x:4d}: {checks}")

    print(f"\n解的周期性：")
    print(f"  解的最小周期 = {M} = {'×'.join(str(m) for m in moduli)} (互质乘积)")
    print(f"  任意解 x + {M}*k 也是解（k为任意整数）")


def demonstrate_rsa_speedup():
    """
    演示CRT在RSA解密中的加速效果。
    """
    print("\n" + "=" * 60)
    print("CRT加速RSA解密演示")
    print("=" * 60)

    # 模拟RSA参数（实际中应为大素数）
    p = 61
    q = 53
    n = p * q
    phi_n = (p - 1) * (q - 1)
    e = 17

    # 私钥 d = e^{-1} mod φ(n)
    d = modular_inverse(e, phi_n)

    # 原始消息
    plaintext_original = 42
    ciphertext = pow(plaintext_original, e, n)

    print(f"\nRSA参数（简化示例）：")
    print(f"  p = {p}, q = {q}")
    print(f"  n = p*q = {n}")
    print(f"  公钥 (e, n) = ({e}, {n})")
    print(f"  私钥 d = e⁻¹ mod φ(n) = {d}")
    print(f"\n加解密测试：")
    print(f"  原始消息 M = {plaintext_original}")
    print(f"  密文 C = M^e mod n = {ciphertext}")

    # 标准RSA解密
    plaintext_std = pow(ciphertext, d, n)

    # CRT加速解密
    plaintext_crt = rsa_crt_speedup(ciphertext, d, p, q)

    print(f"\n解密结果：")
    print(f"  标准RSA: {plaintext_std}")
    print(f"  CRT加速: {plaintext_crt}")
    print(f"  {'✓ 一致' if plaintext_std == plaintext_crt else '✗ 不一致'}")


# =============================================================================
# 测试 - Tests
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("中国剩余定理（CRT）应用测试")
    print("=" * 60)

    # 基础CRT测试
    print("\n基础CRT测试（模数互质）：")
    test_cases = [
        ([2, 3, 2], [3, 5, 7], 23, 105, "孙子算经问题"),
        ([1, 2, 3], [3, 4, 5], 142, 60, "综合剩余定理"),
        ([0, 1, 0, 1], [2, 3, 4, 5], 49, 60, "二进制表示"),
    ]

    for remainders, moduli, expected, _, desc in test_cases:
        solution, M = crt_standard(remainders, moduli)
        status = "✓" if solution == expected else "✗"
        print(f"  {status} [{desc}]")
        print(f"      输入: remainders={remainders}, moduli={moduli}")
        print(f"      解: x = {solution} (mod {M})")
        print(f"      验证: " + " ".join(f"mod{m}={solution%m}" for m in moduli))

    # 扩展CRT测试
    print("\n扩展CRT测试（模数不互质）：")
    ext_cases = [
        ([2, 3], [4, 6], True, "有解情况"),
        ([2, 4], [4, 6], False, "无解情况"),
        ([0, 3, 4], [4, 5, 7], True, "混合情况"),
    ]

    for remainders, moduli, expect_sol, desc in ext_cases:
        has_sol, solution, lcm = crt_extended(remainders, moduli)
        status = "✓" if has_sol == expect_sol else "✗"
        print(f"  {status} [{desc}]")
        print(f"      输入: remainders={remainders}, moduli={moduli}")
        if has_sol:
            print(f"      解: x = {solution} (mod {lcm})")
        else:
            print(f"      结果: 无解")

    # 秘密共享演示
    print("\n秘密共享CRT演示：")
    secret = 12345
    shares = [(101, secret % 101), (103, secret % 103), (107, secret % 107)]
    print(f"  秘密 S = {secret}")
    print(f"  分享 (m_i, a_i): " + " ".join(f"({m},{a})" for m, a in shares))
    recovered = secret_sharing_crt(secret, shares)
    print(f"  CRT恢复: {recovered}")
    print(f"  {'✓ 正确' if recovered == secret else '✗ 错误'}")

    # CRT可视化演示
    demonstrate_crt_visual()

    # RSA CRT加速
    demonstrate_rsa_speedup()
