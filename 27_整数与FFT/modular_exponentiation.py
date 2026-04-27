# -*- coding: utf-8 -*-

"""

算法实现：27_整数与FFT / modular_exponentiation



本文件实现 modular_exponentiation 相关的算法功能。

"""



def binary_exp(base: int, exp: int, mod: int) -> int:

    """

    二进制幂（快速幂）- 迭代版



    参数：

        base: 底数

        exp: 指数（非负整数）

        mod: 模数



    返回：

        base^exp mod mod



    算法步骤：

        1. result = 1

        2. base = base mod mod

        3. 当 exp > 0：

           - 如果 exp 的最低位是 1，result = result * base mod mod

           - base = base * base mod mod

           - exp 右移一位（除以2）

    """

    result = 1

    base = base % mod

    while exp > 0:

        # 如果当前位是 1，乘以 base

        if exp & 1:

            result = (result * base) % mod

        # 平方

        base = (base * base) % mod

        # 右移

        exp >>= 1

    return result





def binary_exp_recursive(base: int, exp: int, mod: int) -> int:

    """

    二进制幂 - 递归版



    递归思路：

        - 如果 exp 是偶数：a^e = (a^(e/2))^2

        - 如果 exp 是奇数：a^e = a * a^(e-1)

    """

    if exp == 0:

        return 1 % mod

    if exp == 1:

        return base % mod



    if exp & 1:

        # 奇数：a^e = a * a^(e-1)

        return (base * binary_exp_recursive(base, exp - 1, mod)) % mod

    else:

        # 偶数：a^e = (a^(e/2))^2

        half = binary_exp_recursive(base, exp >> 1, mod)

        return (half * half) % mod





def montgomery_reduction(a: int, mod: int, inv: int, r: int) -> int:

    """

    蒙哥马利约简



    参数：

        a: 要约简的数

        mod: 模数

        inv: mod 关于 2^r 的模逆元（-mod^(-1) mod 2^r）

        r: 2^r > mod



    返回：

        a * 2^(-r) mod mod



    注意：这是蒙哥马利乘法的核心步骤，需要前置计算 inv = -mod^(-1) mod 2^r

    """

    # t = (a + ((a * inv) mod 2^r) * mod) / 2^r

    t = (a + ((a * inv) & (r - 1)) * mod) >> (r.bit_length() - 1)

    if t >= mod:

        t -= mod

    return t





def montgomery_power(base: int, exp: int, mod: int) -> int:

    """

    蒙哥马利幂乘



    优势：所有模乘都在蒙哥马利域中进行，避免大数溢出



    步骤：

        1. R = 2^r mod mod, inv = -mod^(-1) mod 2^r

        2. 将 base 转为蒙哥马利域：base' = base * R mod mod

        3. 二进制幂（使用蒙哥马利约简）

        4. 将结果转回普通域：result = result * R^(-1) mod mod

    """

    # 计算 r：满足 2^r > mod

    r = 1

    while (1 << r) <= mod:

        r += 1

    r_bit = 1 << r



    # 计算 inv = -mod^(-1) mod 2^r

    inv = mod

    for _ in range(r):

        inv = inv * (2 - inv * mod)

    inv = inv & (r_bit - 1)



    # R = 2^r mod mod

    R = r_bit % mod

    R_inv = montgomery_reduction(1, mod, inv, r_bit)



    # 转换到蒙哥马利域

    base_m = (base * R) % mod



    # 蒙哥马利域中的幂

    result = R % mod  # = 1 in Montgomery form

    while exp > 0:

        if exp & 1:

            result = (result * base_m) % mod

            result = montgomery_reduction(result, mod, inv, r_bit)

        base_m = (base_m * base_m) % mod

        base_m = montgomery_reduction(base_m, mod, inv, r_bit)

        exp >>= 1



    # 转回普通域

    result = montgomery_reduction(result, mod, inv, r_bit)

    return result





def pow_mod_pythonic(base: int, exp: int, mod: int) -> int:

    """

    Python风格：使用 pow 内置函数（仅供参考）



    Python 的 pow(base, exp, mod) 已经非常高效，

    这里仅作为对比参考。

    """

    return pow(base, exp, mod)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 模幂运算测试 ===\n")



    # 测试用例

    test_cases = [

        (2, 10, 1000),      # 2^10 mod 1000 = 1024 mod 1000 = 24

        (3, 100, 1000000),   # 大指数

        (7, 256, 13),        # 小模数

        (12345, 6789, 99991),  # 实际应用场景

        (2, 1000, 1),        # 模数为1的特殊情况

    ]



    print("二进制幂（迭代版）:")

    for base, exp, mod in test_cases:

        result = binary_exp(base, exp, mod)

        expected = pow(base, exp, mod)

        status = "✅" if result == expected else "❌"

        print(f"  {base}^{exp} mod {mod} = {result} {status}")



    print("\n二进制幂（递归版）:")

    for base, exp, mod in test_cases:

        result = binary_exp_recursive(base, exp, mod)

        expected = pow(base, exp, mod)

        status = "✅" if result == expected else "❌"

        print(f"  {base}^{exp} mod {mod} = {result} {status}")



    print("\n蒙哥马利幂乘:")

    for base, exp, mod in test_cases:

        if mod > 0 and mod < 100000:  # 蒙哥马利适合中等大小模数

            result = montgomery_power(base, exp, mod)

            expected = pow(base, exp, mod)

            status = "✅" if result == expected else "❌"

            print(f"  {base}^{exp} mod {mod} = {result} {status}")



    print("\n=== RSA 示例 ===")

    # RSA 加密示例

    p, q = 61, 53  # 两个素数

    n = p * q      # 模数

    phi = (p - 1) * (q - 1)

    e = 17          # 公钥指数

    d = 2753       # 私钥指数（e的模逆）



    message = 42

    # 加密：c = m^e mod n

    ciphertext = binary_exp(message, e, n)

    print(f"原始消息: {message}")

    print(f"加密后: {ciphertext}")

    # 解密：m = c^d mod n

    decrypted = binary_exp(ciphertext, d, n)

    print(f"解密后: {decrypted}")



    # 性能测试

    import time

    print("\n=== 性能测试 ===")

    base, exp, mod = 3, 10**6, 10**12

    start = time.time()

    for _ in range(100):

        binary_exp(base, exp, mod)

    elapsed = time.time() - start

    print(f"二进制幂（迭代）100次: {elapsed:.4f}s")

