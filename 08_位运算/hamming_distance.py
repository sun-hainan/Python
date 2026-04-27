# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / hamming_distance

本文件实现 hamming_distance 相关的算法功能。
"""

def hamming_distance(x: int, y: int) -> int:
    """计算x和y之间的汉明距离（异或后popcount）"""
    diff = x ^ y
    count = 0
    while diff:
        diff &= diff - 1  # 消除最低位的1
        count += 1
    return count

def hamming_distance_lookup(x: int, y: int) -> int:
    """预计算查表法（适合频繁调用场景）"""
    # 256项1字节popcount表
    table = [bin(i).count('1') for i in range(256)]
    diff = x ^ y
    return (
        table[diff & 0xFF] +
        table[(diff >> 8) & 0xFF] +
        table[(diff >> 16) & 0xFF] +
        table[(diff >> 24) & 0xFF]
    )

def hamming_weight(n: int) -> int:
    """计算n的汉明权重（1的个数）"""
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count

def nearest_power_of_two(n: int) -> int:
    """找到与n汉明距离最小的2的幂次"""
    if n <= 0:
        return 1
    # 二进制中只有一个1的数
    msb = 1 << (n.bit_length() - 1)
    # 次高位的2的幂
    candidate2 = msb << 1
    # 比较距离
    d1 = hamming_distance(n, msb)
    d2 = hamming_distance(n, candidate2) if candidate2 > n else float('inf')
    return msb if d1 <= d2 else candidate2

def hamming_distance_array(arr1: list[int], arr2: list[int]) -> list[int]:
    """计算两个等长数组的逐元素汉明距离"""
    assert len(arr1) == len(arr2)
    return [hamming_distance(a, b) for a, b in zip(arr1, arr2)]


if __name__ == "__main__":
    test_pairs = [
        (1, 4),      # 1=0001, 4=0100 -> 2位不同
        (31, 14),    # 31=11111, 14=01110 -> 4位不同
        (0xFF, 0x00), # 8位全不同
        (0b10101010, 0b01010101),  # 8位全不同
        (128, 1),   # 只有最高位和最低位不同 -> 2
    ]

    print("=== 汉明距离测试 ===")
    for x, y in test_pairs:
        d = hamming_distance(x, y)
        print(f"hamming_distance({x}, {y}) = {d}")
        print(f"  {x:08b} XOR {y:08b} = {x^y:08b}")

    # popcount表对比
    print("\n=== popcount性能对比 ===")
    import time
    n = 0x12345678
    iters = 1_000_000

    start = time.perf_counter()
    for _ in range(iters):
        _ = hamming_weight(n)
    t1 = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iters):
        _ = bin(n).count('1')
    t2 = time.perf_counter() - start

    print(f"Brian Kernighan: {t1:.4f}s")
    print(f"bin().count('1'): {t2:.4f}s")
    print(f"加速比: {t2/t1:.1f}x")

    # 数组批量处理
    print("\n=== 批量汉明距离 ===")
    a = [0b1100, 0b1010, 0b1111]
    b = [0b1001, 0b1000, 0b0000]
    distances = hamming_distance_array(a, b)
    print(f"数组A: {[bin(x) for x in a]}")
    print(f"数组B: {[bin(x) for x in b]}")
    print(f"距离: {distances}")
