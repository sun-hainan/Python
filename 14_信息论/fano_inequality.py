# -*- coding: utf-8 -*-
"""
算法实现：14_信息论 / fano_inequality

本文件实现 fano_inequality 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Dict
import math


def binary_entropy(p: float) -> float:
    """计算二元熵函数 H(p) = -p log2(p) - (1-p) log2(1-p)"""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def fano_inequality_bound_H_given_Y(n_states: int, p_error: float) -> float:
    """
    费诺不等式给出条件熵下界

    H(X|Y) >= H(P_e) + P_e * log(|X|-1)

    参数:
        n_states: 信源状态数 |X|
        p_error: 错误概率 P_e = P(X != X_hat)

    返回:
        H(X|Y) >= bound (bit)
    """
    H_Pe = binary_entropy(p_error)
    additional = p_error * math.log2(n_states - 1 + 1e-10)
    return H_Pe + additional


def fano_inequality_bound_error(H_XY: float, n_states: int) -> float:
    """
    费诺不等式给出错误概率下界

    由 H(X|Y) >= H(P_e) + P_e * log(|X|-1) 反解 P_e

    对于二元信源：H(X|Y) >= H(P_e)，反函数

    参数:
        H_XY: 条件熵 H(X|Y)
        n_states: 信源状态数 |X|

    返回:
        P_e >= 下界
    """
    if n_states == 2:
        if H_XY <= 0:
            return 0.0
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2
            if binary_entropy(mid) < H_XY:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    else:
        return max(0.0, H_XY / math.log2(n_states + 1e-10))


def converse_shannon_code(n_bits: int, n_codewords: int, min_error_prob: float) -> Tuple[float, float]:
    """
    利用费诺不等式证明信源编码的逆定理（下界）

    对于长度n的码字和M个码字：
    P_e >= 1 - (H(U) + 1) / n * log2(M)

    参数:
        n_bits: 码字长度（比特数）
        n_codewords: 码字数量M
        min_error_prob: 最小错误概率要求

    返回:
        (rate_lower_bound, info_length_bits)
    """
    log_M = math.log2(n_codewords)
    rate_upper = log_M / n_bits
    rate_bound = 1 - min_error_prob - 1/n_bits
    return rate_bound, rate_upper


def data_processing_bound(H_X: float, H_Y_given_X: float, H_Z_given_Y: float) -> float:
    """
    数据处理不等式（Data Processing Inequality）的费诺变体

    X -> Y -> Z 形成马尔可夫链
    则 H(X|Z) >= H(X|Y) - H(Z|Y)

    参数:
        H_X: H(X)
        H_Y_given_X: H(Y|X)
        H_Z_given_Y: H(Z|Y)

    返回:
        H(X|Z) 的下界
    """
    H_Y = H_X - H_Y_given_X
    H_Z = H_Y - H_Z_given_Y
    I_XY = H_Y - H_Y_given_X
    H_XZ = H_X - I_XY
    return max(0.0, H_XZ)


if __name__ == '__main__':
    print('=== 费诺不等式测试 ===')

    print('--- 测试1: 费诺不等式 H(X|Y) >= H(P_e) + P_e*log(|X|-1) ---')
    n_states = 256
    print(f'字母表大小 |X| = {n_states}')
    print(f'{"P_e":>8}  {"H(P_e)":>10}  {"P_e*log(|X|-1)":>18}  {"H(X|Y)下界":>12}')
    print('  ' + '-' * 55)
    for p_error in [0.01, 0.05, 0.1, 0.2, 0.3, 0.5]:
        H_Pe = binary_entropy(p_error)
        bound = fano_inequality_bound_H_given_Y(n_states, p_error)
        extra = p_error * math.log2(n_states - 1)
        bar = '#' * int(bound * 3)
        print(f'  {p_error:8.2f}  {H_Pe:10.4f}  {extra:18.4f}  {bound:12.4f} |{bar}')

    print('--- 测试2: 从H(X|Y)推导P_e下界（二元信源）---')
    for H_XY in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        p_e_bound = fano_inequality_bound_error(H_XY, n_states=2)
        print(f'  H(X|Y) = {H_XY:.2f} -> P_e >= {p_e_bound:.4f}')

    print('--- 测试3: 信源编码逆定理（费诺不等式应用）---')
    n = 1000
    M = 32
    print(f'码字长度 n={n}, 码字数 M={M}')
    for target_p_e in [0.01, 0.05, 0.1]:
        bound, rate = converse_shannon_code(n, M, target_p_e)
        print(f'  目标P_e={target_p_e}: 率上界={rate:.4f}, 所需码率<={bound:.4f}')

    print('--- 测试4: 不同字母表下的费诺边界 ---')
    for n_states in [2, 4, 8, 16, 32, 256]:
        p_e = 0.1
        bound = fano_inequality_bound_H_given_Y(n_states, p_e)
        print(f'  |X|={n_states:3d}: H(X|Y) >= {bound:.4f} bits')

    print('--- 测试5: 数据处理不等式 ---')
    H_X = 4.0
    H_Y_given_X = 0.5
    H_Z_given_Y = 0.3
    H_XZ_bound = data_processing_bound(H_X, H_Y_given_X, H_Z_given_Y)
    print(f'  H(X)={H_X}, H(Y|X)={H_Y_given_X}, H(Z|Y)={H_Z_given_Y}')
    print(f'  H(X|Z) >= {H_XZ_bound:.4f}')
