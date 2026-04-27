# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / golomb_coding



本文件实现 golomb_coding 相关的算法功能。

"""



import math

from typing import Tuple





def golomb_encode(n: int, m: int) -> Tuple[int, int, str]:

    """

    Golomb 编码一个非负整数 n，参数为 m



    返回：(q, r, 编码字符串)

    """

    q = n // m

    r = n % m



    # 计算 r 的二进制位数

    b = math.ceil(math.log2(m))



    # 如果 r < 2^b - m，用 b-1 位表示

    if 2 ** b - m > r:

        b = b - 1



    # r 的二进制表示（截断二进制编码）

    r_binary = format(r, f"0{b}b") if b > 0 else ""



    # q 的一元编码：一串1后跟一个0

    q_unary = "1" * q + "0"



    return q, r, q_unary + r_binary





def golomb_decode(encoded: str, m: int) -> Tuple[int, int, str]:

    """

    解码 Golomb 编码



    返回：(q, r, 剩余编码)

    """

    # 解码一元部分（q个1后跟一个0）

    q = 0

    pos = 0

    while pos < len(encoded) and encoded[pos] == "1":

        q += 1

        pos += 1



    # 跳过终止的0

    if pos < len(encoded) and encoded[pos] == "0":

        pos += 1



    # 计算 b

    b = math.ceil(math.log2(m))

    if 2 ** b - m > 0:

        # 需要检查是否用 b-1 位

        # 简化处理：假设使用标准的截断二进制编码

        pass



    # 解码 r（二进制部分）

    r = 0

    if b > 0 and pos < len(encoded):

        r_binary = encoded[pos:pos+b]

        if len(r_binary) < b:

            # 不够位，用实际位数

            r = int(r_binary, 2) if r_binary else 0

        else:

            threshold = 2 ** b - m

            if r_binary and int(r_binary, 2) >= threshold:

                # 需要多加一个位

                r_bit = int(r_binary, 2) - threshold

                r = r_bit + threshold if b > 1 else r_bit

            else:

                r = int(r_binary, 2)



    n = q * m + r

    remaining = encoded[pos+b:] if pos + b < len(encoded) else ""



    return n, q, remaining





def encode_string(text: str, m: int) -> str:

    """编码整个字符串（每个字符转为ASCII码再编码）"""

    result = []

    for char in text:

        n = ord(char)

        _, _, code = golomb_encode(n, m)

        result.append(code)

    return "".join(result)





def decode_string(encoded: str, m: int) -> str:

    """解码整个字符串"""

    result = []

    pos = 0

    while pos < len(encoded):

        n, q, remaining = golomb_decode(encoded[pos:], m)

        result.append(chr(n))

        pos = len(encoded) - len(remaining)

    return "".join(result)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Golomb 编码测试 ===\n")



    # 测试参数 m

    m_values = [4, 8, 16, 32]



    for m in m_values:

        print(f"--- m = {m} ---")

        print("参数: b = ceil(log2({m})) = {b}".format(m=m, b=math.ceil(math.log2(m))))



        # 测试编码

        for n in [0, 1, 2, 5, 10, 15, 20, 31, 63]:

            q, r, code = golomb_encode(n, m)

            print(f"  n={n:3d} -> q={q:2d}, r={r:2d}, 编码={code}")



        print()



    # 编码效率测试

    print("=== 编码效率测试 ===")

    m = 16

    print(f"参数 m = {m}")



    # 测试分布：大多数数字小于m，少数大于m

    test_nums = list(range(0, 100, 5))



    total_original_bits = sum(math.ceil(math.log2(n+1)) if n > 0 else 1 for n in test_nums)

    total_encoded_bits = sum(len(golomb_encode(n, m)[2]) for n in test_nums)



    print(f"原始编码总bit数: {total_original_bits}")

    print(f"Golomb编码总bit数: {total_encoded_bits}")

    print(f"压缩比: {total_original_bits / total_encoded_bits:.2f}")



    # 与定长编码对比

    fixed_bits = sum(math.ceil(math.log2(max(test_nums)+1)) for _ in test_nums)

    print(f"定长编码总bit数: {fixed_bits}")

    print(f"Golomb vs 定长: {fixed_bits / total_encoded_bits:.2f}x")



    print()



    # 字符串编码测试

    print("=== 字符串编码测试 ===")

    text = "Hello, World!"

    print(f"原文: '{text}'")



    encoded = encode_string(text, m=16)

    print(f"编码: {encoded}")

    print(f"编码长度: {len(encoded)} bits")



    decoded = decode_string(encoded, m=16)

    print(f"解码: '{decoded}'")

    print(f"验证: {'✅ 通过' if decoded == text else '❌ 失败'}")

