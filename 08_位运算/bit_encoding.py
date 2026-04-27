# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / bit_encoding

本文件实现 bit_encoding 相关的算法功能。
"""

def unary_encode(n: int) -> str:
    """一元编码：n个1后跟一个0"""
    assert n >= 0
    return "1" * n + "0"


def unary_decode(bitstream: str, pos: int) -> tuple[int, int]:
    """一元编码解码：返回(n, next_pos)"""
    n = 0
    while pos < len(bitstream) and bitstream[pos] == "1":
        n += 1
        pos += 1
    # 跳过终止的0
    if pos < len(bitstream):
        pos += 1
    return n, pos


def elias_gamma_encode(n: int) -> str:
    """
    Elias Gamma编码：
    1. 将n表示为二进制（去掉最高位的1）
    2. 用L-1个0前缀（其中L是二进制长度）
    3. 接上剩余的二进制位
    """
    assert n > 0
    binary = bin(n)[3:]  # 去掉'0b'和最高位的1
    return "0" * len(binary) + binary


def elias_gamma_decode(bitstream: str, pos: int) -> tuple[int, int]:
    """Elias Gamma解码"""
    # 读取前导0的数量
    leading_zeros = 0
    while pos < len(bitstream) and bitstream[pos] == "0":
        leading_zeros += 1
        pos += 1

    if pos >= len(bitstream):
        return 0, pos

    # 读取L位（包含最高位的1）
    length = leading_zeros + 1
    bits = bitstream[pos:pos + length]
    if len(bits) < length:
        pos = len(bitstream)
        return 0, pos

    value = int("1" + bits, 2)  # 补上最高位的1
    return value, pos + length


def elias_delta_encode(n: int) -> str:
    """
    Elias Delta编码（更高效）：
    1. 先编码L = floor(log2(n)) + 1 的一元编码
    2. 然后编码(L-1)的二进制（去掉最高位1）
    3. 最后接上n的二进制（去掉最高位1）
    """
    assert n > 0
    L = n.bit_length()  # n的二进制长度
    # 第一部分：L的一元编码
    first_part = "0" * (L - 1) + "1"
    # 第二部分：L-1的二进制（长度是L-1位）
    second_length = L.bit_length() - 1
    second_part = bin(L)[2:].zfill(second_length)[1:]  # 去掉最高位的1
    # 第三部分：n的二进制（去掉最高位的1）
    third_part = bin(n)[3:]  # 去掉'0b'和最高位
    return first_part + second_part + third_part


def elias_delta_decode(bitstream: str, pos: int) -> tuple[int, int]:
    """Elias Delta解码"""
    # 读取L的一元编码
    L = 0
    while pos < len(bitstream) and bitstream[pos] == "0":
        L += 1
        pos += 1
    pos += 1  # 跳过终止的1
    L += 1

    # 读取第二部分：L-1的二进制
    second_length = L.bit_length() - 1
    if second_length > 0:
        second_bits = bitstream[pos:pos + second_length]
        if len(second_bits) < second_length:
            return 0, len(bitstream)
        L_value = int("1" + second_bits, 2)
        pos += second_length
    else:
        L_value = 1

    # 读取第三部分：n的二进制
    third_bits = bitstream[pos:pos + L_value - 1]
    if len(third_bits) < L_value - 1:
        return 0, len(bitstream)
    value = int("1" + third_bits, 2)
    return value, pos + L_value - 1


if __name__ == "__main__":
    test_nums = [1, 2, 3, 7, 15, 16, 31, 63, 64, 100, 255, 256, 1024]

    print("=== 一元编码 ===")
    for n in [1, 2, 3, 5]:
        code = unary_encode(n)
        decoded, _ = unary_decode(code, 0)
        print(f"n={n}: '{code}' -> 解码={decoded}")

    print("\n=== Elias Gamma编码 ===")
    for n in test_nums[:8]:
        code = elias_gamma_encode(n)
        decoded, _ = elias_gamma_decode(code, 0)
        status = "✓" if decoded == n else "✗"
        print(f"n={n:4d}: '{code}' -> 解码={decoded} {status}")
        print(f"       二进制={bin(n)}")

    print("\n=== Elias Delta编码 ===")
    for n in test_nums:
        code = elias_delta_encode(n)
        decoded, _ = elias_delta_decode(code, 0)
        status = "✓" if decoded == n else "✗"
        print(f"n={n:4d}: '{code}' (len={len(code)}) -> {decoded} {status}")

    # 编码效率对比
    print("\n=== 编码长度对比 ===")
    print(f"{'n':>6} {'固定64位':>10} {'Gamma':>8} {'Delta':>8}")
    for n in [100, 1000, 10000, 65535, 100000]:
        fixed = 64
        gamma = len(elias_gamma_encode(n))
        delta = len(elias_delta_encode(n))
        print(f"{n:6d} {fixed:10d} {gamma:8d} {delta:8d}")
