# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / bit_scan_reverse

本文件实现 bit_scan_reverse 相关的算法功能。
"""

def find_first_set(x: int) -> int:
    """
    找到最低位的1（FFS / Find First Set）
    等价于 ctz(x)（count trailing zeros）
    当x=0时返回0
    """
    if x == 0:
        return 0
    return (x & -x).bit_length()  # 最低位的1转为位置


def count_trailing_zeros(x: int) -> int:
    """计算末尾连续0的数量（CTZ）"""
    if x == 0:
        return 0
    count = 0
    while (x & 1) == 0:
        x >>= 1
        count += 1
    return count


def count_leading_zeros(x: int, word_size: int = 64) -> int:
    """计算高位连续0的数量（CLZ / Count Leading Zeros）"""
    if x == 0:
        return word_size
    count = 0
    msb = 1 << (word_size - 1)
    while (x & msb) == 0:
        x <<= 1
        count += 1
    return count


def reverse_bit_order_32(val: int) -> int:
    """32位整数的位顺序反转"""
    # 分阶段交换：1位→2位→4位→8位→16位
    # 第一步：相邻位交换
    val = ((val & 0xAAAAAAAA) >> 1) | ((val & 0x55555555) << 1)
    # 第二步：相邻2位组交换
    val = ((val & 0xCCCCCCCC) >> 2) | ((val & 0x33333333) << 2)
    # 第三步：相邻4位组交换
    val = ((val & 0xF0F0F0F0) >> 4) | ((val & 0x0F0F0F0F) << 4)
    # 第四步：交换高低字节
    val = ((val & 0xFF00FF00) >> 8) | ((val & 0x00FF00FF) << 8)
    # 第五步：反转全部32位（移位合并）
    return ((val >> 16) | (val << 16)) & 0xFFFFFFFF


def reverse_byte_order_32(val: int) -> int:
    """32位整数字节顺序反转（大端↔小端）"""
    return (
        ((val & 0x000000FF) << 24) |
        ((val & 0x0000FF00) << 8) |
        ((val & 0x00FF0000) >> 8) |
        ((val & 0xFF000000) >> 24)
    )


def reverse_byte_order_64(val: int) -> int:
    """64位整数字节顺序反转"""
    val = ((val & 0xFF00FF00FF00FF00) >> 8) | ((val & 0x00FF00FF00FF00FF) << 8)
    val = ((val & 0xFFFF0000FFFF0000) >> 16) | ((val & 0x0000FFFF0000FFFF) << 16)
    return ((val >> 32) | (val << 32)) & 0xFFFFFFFFFFFFFFFF


def swap_endian_16(val: int) -> int:
    """16位半字节交换"""
    return ((val & 0xFF) << 8) | ((val >> 8) & 0xFF)


def reverse_bits_table() -> list[int]:
    """构建256项位反转查找表（用于处理字节）"""
    table = [0] * 256
    for i in range(256):
        reversed_val = 0
        for j in range(8):
            reversed_val = (reversed_val << 1) | ((i >> j) & 1)
        table[i] = reversed_val
    return table


# 预计算位反转表
REVERSE_TABLE = reverse_bits_table()


def reverse_byte_slow(val: int) -> int:
    """字节内位反转（朴素实现）"""
    result = 0
    for i in range(8):
        result = (result << 1) | ((val >> i) & 1)
    return result


def reverse_byte_fast(val: int) -> int:
    """字节内位反转（查表实现）"""
    return REVERSE_TABLE[val & 0xFF]


if __name__ == "__main__":
    print("=== 位扫描操作 ===")
    test_vals = [0b00101100, 0b10000000, 0b00001000, 0b11111111, 0]
    for v in test_vals:
        ffs = find_first_set(v)
        ctz = count_trailing_zeros(v)
        clz = count_leading_zeros(v, 8)
        print(f"v={v:08b}: FFS={ffs}, CTZ={ctz}, CLZ(8bit)={clz}")

    print("\n=== 32位位反转 ===")
    test_32 = [0x12345678, 0xAAAAAAAA, 0x55555555]
    for val in test_32:
        reversed_val = reverse_bit_order_32(val)
        print(f"0x{val:08X} -> 0x{reversed_val:08X}")
        # 验证：反转两次回到原值
        double_rev = reverse_bit_order_32(reversed_val)
        status = "✓" if double_rev == val else "✗"
        print(f"  双重反转验证: {status}")

    print("\n=== 字节序反转 ===")
    val = 0x12345678
    print(f"原值: 0x{val:08X} = {val}")
    print(f"大端→小端: 0x{reverse_byte_order_32(val):08X}")
    val64 = 0x123456789ABCDEF0
    print(f"64位: 0x{val64:016X} -> 0x{reverse_byte_order_64(val64):016X}")

    print("\n=== 字节内位反转（查表 vs 朴素） ===")
    import time
    test_bytes = list(range(256))
    iters = 100000

    start = time.perf_counter()
    for _ in range(iters):
        for b in test_bytes:
            _ = reverse_byte_slow(b)
    t_slow = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iters):
        for b in test_bytes:
            _ = reverse_byte_fast(b)
    t_fast = time.perf_counter() - start

    print(f"朴素实现: {t_slow:.4f}s")
    print(f"查表实现: {t_fast:.4f}s")
    print(f"加速比: {t_slow/t_fast:.1f}x")
