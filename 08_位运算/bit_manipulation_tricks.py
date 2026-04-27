# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / bit_manipulation_tricks

本文件实现 bit_manipulation_tricks 相关的算法功能。
"""

def is_odd(n: int) -> bool:
    """奇偶性判断：n & 1 == 1 则为奇数"""
    return (n & 1) == 1

def is_power_of_two(n: int) -> bool:
    """判断是否2的幂次：n > 0 且 n & (n-1) == 0"""
    return n > 0 and (n & (n - 1)) == 0

def extract_lsb(n: int) -> int:
    """提取最低有效位（最低位的1）：n & (-n)"""
    return n & (-n)

def clear_lsb(n: int) -> int:
    """清除最低有效位：n & (n - 1)"""
    return n & (n - 1)

def count_ones(n: int) -> int:
    """位计数（Brian Kernighan算法）：O(k)，k为1的位数"""
    count = 0
    while n:
        n &= n - 1  # 消除最低位的1
        count += 1
    return count

def reverse_bits(n: int, width: int = 32) -> int:
    """二进制翻转：逐位交换"""
    result = 0
    for i in range(width):
        result <<= 1
        result |= (n >> i) & 1
    return result

def reverse_bytes_32(val: int) -> int:
    """32位整数字节反转"""
    return (
        ((val >> 24) & 0xFF) |
        ((val >> 8)  & 0xFF00) |
        ((val << 8)  & 0xFF0000) |
        ((val << 24) & 0xFF000000)
    )

def swap_two(a: int, b: int) -> tuple[int, int]:
    """不用临时变量交换两数"""
    a ^= b
    b ^= a
    a ^= b
    return a, b

def bit_length_of_int(n: int) -> int:
    """获取整数需要的二进制位数"""
    return n.bit_length()

def mask_low_k_bits(k: int) -> int:
    """生成低k位全为1的掩码"""
    return (1 << k) - 1

if __name__ == "__main__":
    test_n = 0b10110100
    print(f"原数:      {bin(test_n)} = {test_n}")
    print(f"奇数?      {is_odd(test_n)}")
    print(f"2的幂次?   {is_power_of_two(8)}")
    print(f"最低有效位: {bin(extract_lsb(test_n))} = {extract_lsb(test_n)}")
    print(f"清除LSB:   {bin(clear_lsb(test_n))} = {clear_lsb(test_n)}")
    print(f"1的个数:   {count_ones(test_n)}")
    print(f"二进制翻转: {bin(reverse_bits(test_n, 8))} = {reverse_bits(test_n, 8)}")
    print(f"字节反转:  0x{reverse_bytes_32(0x12345678):08x}")
    a, b = 5, 9
    a, b = swap_two(a, b)
    print(f"交换后: a={a}, b={b}")
    print(f"掩码低3位: {bin(mask_low_k_bits(3))} = {mask_low_k_bits(3)}")
