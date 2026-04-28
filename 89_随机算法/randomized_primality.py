# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / randomized_primality



本文件实现随机化素数测试算法。

素数测试是现代密码学的基础：

    - 费马素数测试（基于费马小定理）

    - Miller-Rabin 素数测试（更可靠，实践中广泛使用）



注意：这些都是概率型测试，可能产生伪素数（假阳性）。
      Miller-Rabin 多轮测试可将错误概率降到任意小。

"""

import random
import math


def modular_exponentiation(base: int, exp: int, mod: int) -> int:
    """
    模幂运算（快速幂）

    计算 (base^exp) % mod，使用二分幂思想，
    时间复杂度 O(log exp)。

    参数：
        base: 底数
        exp: 指数
        mod: 模数

    返回：
        (base^exp) % mod 的结果
    """
    result = 1
    base = base % mod

    while exp > 0:
        # 如果指数为奇数，先乘以 base
        if exp % 2 == 1:
            result = (result * base) % mod
        # 指数减半，底数平方
        exp //= 2
        base = (base * base) % mod

    return result


def fermat_is_prime(n: int, k: int = 10) -> bool:
    """
    费马素数测试（Monte Carlo）

    基于费马小定理：
        如果 p 是素数，a 是任意整数 (1 ≤ a < p)，
        则 a^(p-1) ≡ 1 (mod p)

    测试 k 次随机 a，如果不满足费马条件则 n 一定是合数，
    如果满足则 n 可能是素数（可能是伪素数）。

    参数：
        n: 待测试的正整数
        k: 测试轮数（每轮随机选一个底数）

    返回：
        True 表示 n 可能是素数，False 表示 n 一定是合数
    """
    # 边界情况处理
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    for _ in range(k):
        # 随机选择底数 a，范围 [2, n-2]
        a = random.randint(2, n - 2)

        # 计算 a^(n-1) mod n
        if modular_exponentiation(a, n - 1, n) != 1:
            # 费马条件不满足，一定是合数
            return False

    # 通过所有测试，n 可能是素数
    return True


def miller_rabin_is_prime(n: int, k: int = 10) -> bool:
    """
    Miller-Rabin 素数测试（Monte Carlo，更可靠）

    基于以下原理：
        对于奇素数 p，可以将 n-1 写成 2^r × d 的形式。
        对于任意 a (1 < a < p-1)：
            a^d ≡ 1 (mod p) 或 a^(2^j·d) ≡ -1 (mod p)（对某个 j）

    Miller-Rabin 比费马测试更严格，因为 Carmichael 数
   （一种合数）对费马测试所有底数都通过，但对 Miller-Rabin
    至少有一半的底数能检测出问题。

    参数：
        n: 待测试的正整数
        k: 测试轮数

    返回：
        True 表示 n 可能是素数，False 表示 n 一定是合数
    """
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False

    # 将 n-1 分解为 2^r × d 的形式
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(k):
        a = random.randint(2, n - 2)

        # 计算 x = a^d mod n
        x = modular_exponentiation(a, d, n)

        if x == 1 or x == n - 1:
            # 通过本轮测试
            continue

        # 连续平方 r-1 次
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            # 循环正常结束（未找到 x == n-1），说明 n 是合数
            return False

    # 通过所有测试
    return True


def find_prime(bits: int, k: int = 10) -> int:
    """
    生成指定位数的随机素数

    流程：
        1. 生成指定位数的随机奇数
        2. 用 Miller-Rabin 测试
        3. 通过则返回，否则重新生成

    参数：
        bits: 素数的位数
        k: Miller-Rabin 测试轮数

    返回：
        一个 bits 位的素数
    """
    lower = 1 << (bits - 1)    # 2^(bits-1)
    upper = (1 << bits) - 1    # 2^bits - 1

    while True:
        # 生成 [lower, upper] 范围内的随机奇数
        candidate = random.randrange(lower, upper, 2)

        # 确保最高位是 1（保证位数）
        candidate |= (1 << (bits - 1))

        if miller_rabin_is_prime(candidate, k):
            return candidate


def is_carmichael_number(n: int) -> bool:
    """
    检查 n 是否为 Carmichael 数（伪素数）

    Carmichael 数对所有底数都满足费马小定理，
    但又不是素数。已知有无穷多个，最小的是 561。

    参数：
        n: 待测试的正整数

    返回：
        True 表示 n 是 Carmichael 数
    """
    if fermat_is_prime(n, 20):
        return False  # 可能是素数，不是 Carmichael

    if n % 2 == 0:
        return False

    # 检查所有与 n 互质的底数 a
    for a in range(2, n):
        if math.gcd(a, n) != 1:
            continue
        if modular_exponentiation(a, n - 1, n) != 1:
            return False

    return True


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 随机化素数测试 ===\n")

    random.seed(42)

    # 测试 1: 已知素数和合数
    print("--- Miller-Rabin 素数测试 ---")

    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
              101, 173, 257, 1009, 7919]
    composites = [4, 6, 8, 9, 10, 12, 15, 16, 18, 20, 21, 22, 24, 25, 91, 100, 561]

    print("  素数测试: ", end="")
    prime_ok = all(miller_rabin_is_prime(p, 20) for p in primes)
    print("✅" if prime_ok else "❌")

    print("  合数测试: ", end="")
    composite_ok = all(not miller_rabin_is_prime(c, 20) for c in composites)
    print("✅" if composite_ok else "❌")

    # 测试 2: 大数测试
    print("\n--- 大数素数测试 ---")
    large_numbers = [
        104729,           # 第 10000 个素数
        15485863,         # 第 1000000 个素数
        179424673,        # 第 10000000 个素数
        2**31 - 1,        # Mersenne 素数相关的合数
    ]

    for n in large_numbers:
        result = miller_rabin_is_prime(n, 20)
        print(f"  {n}: {'可能是素数' if result else '是合数'}")

    # 测试 3: 费马测试 vs Miller-Rabin（测试 Carmichael 数）
    print("\n--- 费马 vs Miller-Rabin (Carmichael 数 561) ---")

    n = 561  # 561 = 3 × 11 × 17，是最小的 Carmichael 数
    fermat_result = fermat_is_prime(n, 20)
    mr_result = miller_rabin_is_prime(n, 20)

    print(f"  费马测试: {'可能是素数' if fermat_result else '是合数'}")
    print(f"  Miller-Rabin: {'可能是素数' if mr_result else '是合数'}")
    print(f"  561 实际是合数 (3×11×17)")
    print(f"  费马测试对 Carmichael 数失效，Miller-Rabin 更可靠")

    # 测试 4: 生成随机素数
    print("\n--- 随机素数生成 ---")
    for bits in [16, 32, 64]:
        p = find_prime(bits, k=15)
        print(f"  {bits} 位素数: {p} (长度 {len(bin(p))-2} bits)")

    # 测试 5: 模幂运算验证
    print("\n--- 模幂运算验证 ---")
    test_cases = [
        (2, 10, 1000),
        (3, 7, 13),
        (7, 13, 100),
    ]
    for base, exp, mod in test_cases:
        result = modular_exponentiation(base, exp, mod)
        expected = pow(base, exp) % mod
        status = "✅" if result == expected else "❌"
        print(f"  {base}^{exp} mod {mod} = {result} {status}")

    print("\n说明：")
    print("  - 费马测试：简单但对 Carmichael 数失效")
    print("  - Miller-Rabin：更可靠，实践中使用（k=20 错误率 < 2^-40）")
    print("  - 错误率：(1/4)^k，即每轮错误概率 ≤ 1/4")
    print("  - 实际中 RSA 密钥生成使用 Miller-Rabin")
