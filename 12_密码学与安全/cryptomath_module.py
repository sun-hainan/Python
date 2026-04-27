# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / cryptomath_module



本文件实现 cryptomath_module 相关的算法功能。

"""



import random

import math





def gcd(a: int, b: int) -> int:

    """

    最大公约数（欧几里得算法）



    参数：

        a, b: 两个整数



    返回：gcd(a, b)



    复杂度：时间O(log min(a,b))，空间O(1)

    """

    while b != 0:

        a, b = b, a % b

    return abs(a)





def extended_gcd(a: int, b: int) -> tuple:

    """

    扩展欧几里得算法



    求 ax + by = gcd(a,b) 的解



    参数：

        a, b: 两个整数



    返回：(gcd, x, y) 其中 ax + by = gcd



    复杂度：时间O(log min(a,b))，空间O(1)

    """

    if b == 0:

        return a, 1, 0



    gcd_val, x1, y1 = extended_gcd(b, a % b)

    x = y1

    y = x1 - (a // b) * y1



    return gcd_val, x, y





def mod_inverse(a: int, m: int) -> int:

    """

    模逆元



    求 a^(-1) mod m



    参数：

        a: 底数

        m: 模数



    返回：a的模逆元，不存在返回-1



    复杂度：时间O(log m)

    """

    gcd_val, x, _ = extended_gcd(a, m)



    if gcd_val != 1:

        return -1  # 逆元不存在



    return (x % m + m) % m





def is_prime(n: int) -> bool:

    """

    素数判定（试除法）



    参数：

        n: 待检测的整数



    返回：是否为素数



    复杂度：时间O(sqrt(n))，空间O(1)

    """

    if n < 2:

        return False

    if n == 2:

        return True

    if n % 2 == 0:

        return False



    for i in range(3, int(math.sqrt(n)) + 1, 2):

        if n % i == 0:

            return False



    return True





def is_prime_miller_rabin(n: int, k: int = 10) -> bool:

    """

    Miller-Rabin素数测试（概率算法）



    参数：

        n: 待检测的整数

        k: 测试轮数



    返回：是否为素数（高概率）



    复杂度：时间O(k log^3 n)

    """

    if n < 2:

        return False

    if n == 2 or n == 3:

        return True

    if n % 2 == 0:

        return False



    # 分解 n-1 = d * 2^s

    d = n - 1

    s = 0

    while d % 2 == 0:

        d //= 2

        s += 1



    # 测试k轮

    for _ in range(k):

        a = random.randrange(2, n - 1)

        x = pow(a, d, n)



        if x == 1 or x == n - 1:

            continue



        for _ in range(s - 1):

            x = (x * x) % n

            if x == n - 1:

                break

        else:

            return False



    return True





def euler_totient(n: int) -> int:

    """

    欧拉函数 φ(n)



    返回：1到n中与n互素的数的个数



    复杂度：时间O(sqrt(n))

    """

    result = n

    p = 2



    while p * p <= n:

        if n % p == 0:

            while n % p == 0:

                n //= p

            result -= result // p

        p += 1



    if n > 1:

        result -= result // n



    return result





def fast_power(base: int, exp: int, mod: int) -> int:

    """

    快速幂（模幂运算）



    参数：

        base: 底数

        exp: 指数

        mod: 模数



    返回：base^exp mod mod



    复杂度：时间O(log exp)，空间O(1)



    应用：RSA加密解密

    """

    result = 1

    base = base % mod



    while exp > 0:

        if exp % 2 == 1:

            result = (result * base) % mod

        exp //= 2

        base = (base * base) % mod



    return result





def discrete_log(a: int, b: int, p: int) -> int:

    """

    离散对数（暴力法）



    求 x 使得 a^x ≡ b (mod p)



    参数：

        a, b, p: 素数模p下的参数



    返回：x，不存在返回-1



    复杂度：时间O(p)，空间O(1)



    注意：实际使用Baby-Step-Giant-Step算法更快

    """

    n = int(math.isqrt(p)) + 1



    # Baby steps

    baby = {1: 0}

    for i in range(1, n):

        baby[(a ** i) % p] = i



    # Giant steps

    an = pow(a, -n, p)  # a^(-n) mod p

    gamma = b



    for j in range(n):

        if gamma in baby:

            return j * n + baby[gamma]

        gamma = (gamma * an) % p



    return -1





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 密码学数学基础测试 ===\n")



    # GCD和扩展GCD

    a, b = 35, 15

    g, x, y = extended_gcd(a, b)

    print(f"扩展GCD: gcd({a},{b}) = {g}, x={x}, y={y}")

    print(f"验证: {a}*{x} + {b}*{y} = {a*x + b*y}")



    print()



    # 模逆元

    tests = [(3, 11), (7, 26), (5, 12)]

    for a, m in tests:

        inv = mod_inverse(a, m)

        print(f"模逆元: {a}^(-1) mod {m} = {inv}")

        if inv != -1:

            print(f"  验证: {a} * {inv} mod {m} = {(a * inv) % m}")



    print()



    # 素数判定

    primes = [2, 17, 100, 991, 1000]

    print("素数判定（Miller-Rabin）:")

    for n in primes:

        result = is_prime_miller_rabin(n)

        print(f"  {n}: {'是' if result else '否'} 素数")



    print()



    # 欧拉函数

    n_values = [12, 35, 100]

    print("欧拉函数 φ(n):")

    for n in n_values:

        phi = euler_totient(n)

        print(f"  φ({n}) = {phi}")



    print()



    # 快速幂

    base, exp, mod = 2, 10, 1000

    result = fast_power(base, exp, mod)

    print(f"快速幂: {base}^{exp} mod {mod} = {result}")



    print("\n说明：")

    print("  - 模逆元是RSA解密的核心")

    print("  - Miller-Rabin用于大数素性检测")

    print("  - 欧拉函数用于RSA密钥生成")

