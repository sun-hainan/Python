# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / gray_code

本文件实现 gray_code 相关的算法功能。
"""

def binary_to_gray(n: int) -> int:
    """
    二进制转格雷码：
    原理：最高位不变，其余位 = 当前位 XOR 前一位
    g[i] = b[i] XOR b[i+1]（从MSB向LSB）
    """
    return n ^ (n >> 1)


def gray_to_binary(g: int) -> int:
    """
    格雷码转二进制：
    原理：从最高位开始，依次将格雷码位与已解出的二进制位异或
    b[MSB] = g[MSB]
    b[i] = b[i+1] XOR g[i]
    """
    binary = 0
    while g > 0:
        binary ^= g
        g >>= 1
    return binary


def generate_gray_code_sequence(n_bits: int) -> list[int]:
    """
    生成n位格雷码的完整序列（0到2^n-1）
    特性：首尾相接也只差1位（循环格雷码）
    """
    size = 1 << n_bits
    return [binary_to_gray(i) for i in range(size)]


def generate_gray_code_string(n_bits: int) -> list[str]:
    """生成n位格雷码序列（返回二进制字符串格式）"""
    size = 1 << n_bits
    result = []
    for i in range(size):
        gray = binary_to_gray(i)
        result.append(format(gray, f"0{n_bits}b"))
    return result


def gray_code_position(gray: int, n_bits: int) -> int:
    """查找某格雷码值在序列中的位置（解码）"""
    return gray_to_binary(gray)


def n_th_gray_code(n: int, n_bits: int) -> str:
    """返回第n个格雷码的二进制字符串"""
    gray = binary_to_gray(n)
    return format(gray, f"0{n_bits}b")


def is_gray_code_valid(gray: int, prev_gray: int) -> bool:
    """检查两个格雷码是否只差一位"""
    diff = gray ^ prev_gray
    # 只差一位：popcount == 1
    return (diff & (diff - 1)) == 0


def construct_gray_code_reflect(n_bits: int) -> list[str]:
    """
    用反射法构造格雷码（递归方式）
    1位: 0, 1
    2位: 00,01,11,10（镜像）
    3位: 000,001,011,010,110,111,101,100
    """
    if n_bits == 0:
        return []
    if n_bits == 1:
        return ["0", "1"]

    prev = construct_gray_code_reflect(n_bits - 1)
    result = ["0" + code for code in prev]  # 前半部加0前缀
    reversed_prev = prev[::-1]
    result.extend(["1" + code for code in reversed_prev])  # 后半部加1前缀并镜像
    return result


if __name__ == "__main__":
    # 基本转换测试
    print("=== 二进制↔格雷码 转换 ===")
    for n in [0, 1, 2, 3, 4, 7, 8, 15, 16, 255]:
        g = binary_to_gray(n)
        back = gray_to_binary(g)
        status = "✓" if back == n else "✗"
        print(f"n={n:3d} ({bin(n):>8s}) -> gray={g:3d} ({bin(g):>8s}) -> back={back:3d} {status}")

    # 3位格雷码序列
    print("\n=== 3位格雷码序列（反射法）===")
    codes = construct_gray_code_reflect(3)
    for i, code in enumerate(codes):
        gray_val = int(code, 2)
        print(f"序号{i:2d}: 格雷码={code}, 位置={gray_to_binary(gray_val)}")

    # 验证相邻只差一位
    print("\n=== 验证相邻只差一位 ===")
    gray_seq = generate_gray_code_sequence(4)
    all_valid = True
    for i in range(len(gray_seq) - 1):
        if not is_gray_code_valid(gray_seq[i + 1], gray_seq[i]):
            all_valid = False
            break
    print(f"4位格雷码序列相邻差异验证: {'✓ 通过' if all_valid else '✗ 失败'}")

    # 循环特性（首尾也只差一位）
    print("\n=== 循环特性（首尾差异）===")
    for n_bits in [2, 3, 4, 5]:
        seq = generate_gray_code_sequence(n_bits)
        first_last_diff = seq[0] ^ seq[-1]
        is_single_bit = (first_last_diff & (first_last_diff - 1)) == 0
        print(f"{n_bits}位: 首={bin(seq[0])}, 尾={bin(seq[-1])}, 差={bin(first_last_diff)} -> {'✓循环' if is_single_bit else '✗'}")

    # 应用示例：LED矩阵扫描
    print("\n=== LED矩阵扫描路径 ===")
    print("假设8×8 LED矩阵，使用格雷码路径可避免相邻像素同时切换")
    path = generate_gray_code_string(6)  # 64个位置用6位
    print("前16步:", path[:16])
