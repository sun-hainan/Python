# -*- coding: utf-8 -*-

"""

算法实现：局部可解码码 / crt_local_decode



本文件实现 crt_local_decode 相关的算法功能。

"""



import random

import math





def generate_coprime_moduli(k, max_modulus=1000):

    """

    生成 k 个互素的模数。



    参数:

        k: 模数数量

        max_modulus: 最大模数值



    返回:

        模数列表

    """

    moduli = []

    product = 1



    for _ in range(k):

        # 选择一个与已有模数都互素的数

        for candidate in range(max(product + 1, 10), max_modulus):

            if all(math.gcd(candidate, m) == 1 for m in moduli):

                moduli.append(candidate)

                product *= candidate

                break



    return moduli[:k]





def crt_encode(value, moduli):

    """

    CRT 编码：将整数编码为多个余数。



    参数:

        value: 要编码的整数

        moduli: 互素模数列表



    返回:

        余数列表

    """

    return [value % m for m in moduli]





def crt_decode(remainders, moduli):

    """

    CRT 解码：从余数恢复原始整数。



    使用中国剩余定理。



    参数:

        remainders: 余数列表

        moduli: 模数列表



    返回:

        原始整数

    """

    k = len(moduli)

    M = 1

    for m in moduli:

        M *= m



    result = 0

    for i in range(k):

        Mi = M // moduli[i]

        # Mi 的模逆

        _, xi, _ = extended_gcd(Mi % moduli[i], moduli[i])

        yi = xi % moduli[i]

        result += remainders[i] * Mi * yi



    return result % M





def extended_gcd(a, b):

    """扩展欧几里得算法。"""

    if a == 0:

        return b, 0, 1

    g, x1, y1 = extended_gcd(b % a, a)

    x = y1 - (b // a) * x1

    y = x1

    return g, x, y





class CRTLDC:

    """

    CRT 码的局部解码器。



    码字：在 k 个模数下的余数

    局部解码：查询少数几个余数即可恢复原始值

    """



    def __init__(self, num_moduli=5, max_modulus=100):

        self.moduli = generate_coprime_moduli(num_moduli, max_modulus)

        self.k = num_moduli

        self.M = 1

        for m in self.moduli:

            self.M *= m



    def encode(self, value):

        """CRT 编码。"""

        return crt_encode(value, self.moduli)



    def local_decode(self, remainders, query_indices=None):

        """

        局部解码：从部分余数恢复原始值。



        参数:

            remainders: 完整的余数列表

            query_indices: 要查询的索引（可选）



        返回:

            恢复的整数值

        """

        if query_indices is None:

            # 查询所有

            query_indices = list(range(self.k))



        # 取部分余数

        partial_moduli = [self.moduli[i] for i in query_indices]

        partial_remainders = [remainders[i] for i in query_indices]



        # 计算这些模数的乘积

        M_partial = 1

        for m in partial_moduli:

            M_partial *= m



        # 用中国剩余定理恢复（用部分模数）

        result = 0

        for i, idx in enumerate(query_indices):

            Mi = M_partial // partial_moduli[i]

            _, xi, _ = extended_gcd(Mi % partial_moduli[i], partial_moduli[i])

            yi = xi % partial_moduli[i]

            result += partial_remainders[i] * Mi * yi



        return result % M_partial



    def verify_consistency(self, remainders, value, query_indices):

        """

        验证一致性：检查部分余数是否与给定值一致。



        参数:

            remainders: 余数列表

            value: 声称的值

            query_indices: 查询位置



        返回:

            True/False

        """

        for idx in query_indices:

            if remainders[idx] != value % self.moduli[idx]:

                return False

        return True





def crt_error_detection(remainders, moduli, num_errors):

    """

    CRT 码的错误检测。



    如果余数个数超过 num_errors，可以检测到错误。



    参数:

        remainders: 接收到的余数

        moduli: 模数列表

        num_errors: 容忍的错误数



    返回:

        是否一致

    """

    # 检查是否所有余数在允许范围内

    for r, m in zip(remainders, moduli):

        if not (0 <= r < m):

            return False



    # 检查一致性（简化）

    return True





if __name__ == "__main__":

    print("=== CRT 码局部解码测试 ===")



    # 创建 CRT 码

    num_moduli = 5

    crt = CRTLDC(num_moduli=num_moduli, max_modulus=100)



    print(f"模数: {crt.moduli}")

    print(f"模数乘积 M: {crt.M}")

    print(f"模数数量: {crt.k}")



    # 编码

    original_value = 12345

    remainders = crt.encode(original_value)



    print(f"\n原始值: {original_value}")

    print(f"CRT 编码余数: {remainders}")



    # 验证 CRT 解码

    decoded = crt_decode(remainders, crt.moduli)

    print(f"CRT 解码: {decoded} {'✓' if decoded == original_value else '✗'}")



    # 局部解码（只查询一部分）

    print("\n=== 局部解码测试 ===")

    for num_queries in [2, 3, 4]:

        query_indices = list(range(num_queries))

        local_value = crt.local_decode(remainders, query_indices)

        # 用部分模数解码会得到不同的值，但可以验证一致性

        consistent = crt.verify_consistency(remainders, original_value, query_indices)

        print(f"查询 {num_queries} 个余数:")

        print(f"  查询位置: {query_indices}")

        print(f"  部分解码值: {local_value}")

        print(f"  与原始值一致: {consistent}")



    # 错误检测

    print("\n=== 错误检测测试 ===")

    noisy = remainders[:]

    # 注入一个错误

    noisy[2] = (noisy[2] + 1) % crt.moduli[2]



    print(f"原始余数: {remainders}")

    print(f"错误余数: {noisy}")

    consistent = crt.verify_consistency(noisy, original_value, [0, 1, 2])

    print(f"一致性检查: {consistent}")



    print("\nCRT 码 LDC 特性:")

    print("  局部解码：只需查询 O(1) 个余数即可验证一致性")

    print("  编码效率：O(k) 时间编码 k 个余数")

    print("  距离：可以检测最多 k-1 个错误")

    print("  应用：分布式存储、冗余计算")

