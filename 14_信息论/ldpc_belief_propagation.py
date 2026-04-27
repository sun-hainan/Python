# -*- coding: utf-8 -*-
"""
算法实现：14_信息论 / ldpc_belief_propagation

本文件实现 ldpc_belief_propagation 相关的算法功能。
"""

import numpy as np
from typing import Tuple, List, Dict
import math


def llr_channel(y: np.ndarray, snr_linear: float) -> np.ndarray:
    """
    计算信道输出的对数似然比（LLR）

    对于BPSK调制和AWGN信道：L_ch = 2y/sigma^2
    """
    noise_var = 1.0 / (2 * snr_linear)
    return 2.0 * y / noise_var


def bp_decode(
    H: np.ndarray,
    llr_ch: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-4
) -> Tuple[np.ndarray, int, bool]:
    """
    置信传播（Belief Propagation）译码LDPC码

    使用对数域和积算法（Log-Domain SPA）

    参数:
        H: 校验矩阵（稀疏，0/1）
        llr_ch: 信道LLR（每个比特的后验对数似然）
        max_iter: 最大迭代次数
        tol: 收敛阈值

    返回:
        (codeword, iterations, converged): 译码结果、迭代次数、是否收敛
    """
    m, n = H.shape

    var_to_check = [[] for _ in range(n)]
    check_to_var = [[] for _ in range(m)]
    for i in range(m):
        for j in range(n):
            if H[i, j] == 1:
                var_to_check[j].append(i)
                check_to_var[i].append(j)

    L_q = np.zeros((m, n))
    for j in range(n):
        for i in var_to_check[j]:
            L_q[i, j] = llr_ch[j]

    for iteration in range(max_iter):
        L_r = np.zeros((m, n))
        for i in range(m):
            neighbors = check_to_var[i]
            if len(neighbors) == 0:
                continue

            prod_tanh = np.ones(len(neighbors))
            for idx, j in enumerate(neighbors):
                q_val = L_q[i, j]
                if np.abs(q_val) > 1e-10:
                    prod_tanh[idx] = np.tanh(q_val / 2.0)

            total_prod = np.prod(prod_tanh)

            for idx, j in enumerate(neighbors):
                if len(neighbors) > 1:
                    other_prod = total_prod / (np.tanh(L_q[i, j] / 2.0) + 1e-10)
                    other_prod = np.clip(other_prod, -0.9999, 0.9999)
                    L_r[i, j] = 2.0 * np.arctanh(other_prod)
                else:
                    L_r[i, j] = 0.0

        L_q_new = np.zeros((m, n))
        for j in range(n):
            for i in var_to_check[j]:
                total = llr_ch[j]
                for i2 in var_to_check[j]:
                    if i2 != i:
                        total += L_r[i2, j]
                L_q_new[i, j] = total

        L_q = L_q_new

        L_post = np.zeros(n)
        for j in range(n):
            L_post[j] = llr_ch[j]
            for i in var_to_check[j]:
                L_post[j] += L_r[i, j]

        decoded = np.where(L_post < 0, 1, 0)
        syndrome = np.mod(H.dot(decoded), 2)
        if syndrome.sum() < tol:
            return decoded, iteration + 1, True

    L_post = np.zeros(n)
    for j in range(n):
        L_post[j] = llr_ch[j]
        for i in var_to_check[j]:
            L_post[j] += L_r[i, j]

    decoded = np.where(L_post < 0, 1, 0)
    return decoded, max_iter, False


def min_sum_decode(
    H: np.ndarray,
    llr_ch: np.ndarray,
    max_iter: int = 100
) -> Tuple[np.ndarray, int, bool]:
    """
    最小和算法（Min-Sum Decoding）- BP的简化版本

    用 min(|q|) 近似 product tanh(q/2)

    参数:
        H: 校验矩阵
        llr_ch: 信道LLR
        max_iter: 最大迭代次数

    返回:
        (codeword, iterations, converged)
    """
    m, n = H.shape

    var_to_check = [[] for _ in range(n)]
    check_to_var = [[] for _ in range(m)]
    for i in range(m):
        for j in range(n):
            if H[i, j] == 1:
                var_to_check[j].append(i)
                check_to_var[i].append(j)

    L_q = np.zeros((m, n))
    for j in range(n):
        for i in var_to_check[j]:
            L_q[i, j] = llr_ch[j]

    for iteration in range(max_iter):
        L_r = np.zeros((m, n))
        for i in range(m):
            neighbors = check_to_var[i]
            if len(neighbors) == 0:
                continue

            for idx, j in enumerate(neighbors):
                others = [L_q[i, j2] for j2 in neighbors if j2 != j]
                if len(others) == 0:
                    L_r[i, j] = 0.0
                else:
                    signs = np.prod(np.sign(others))
                    min_mag = np.min(np.abs(others))
                    L_r[i, j] = signs * min_mag

        L_q_new = np.zeros((m, n))
        for j in range(n):
            for i in var_to_check[j]:
                total = llr_ch[j]
                for i2 in var_to_check[j]:
                    if i2 != i:
                        total += L_r[i2, j]
                L_q_new[i, j] = total

        L_q = L_q_new

        L_post = np.zeros(n)
        for j in range(n):
            L_post[j] = llr_ch[j]
            for i in var_to_check[j]:
                L_post[j] += L_r[i, j]

        decoded = np.where(L_post < 0, 1, 0)
        syndrome = np.mod(H.dot(decoded), 2)
        if syndrome.sum() < 1e-4:
            return decoded, iteration + 1, True

    return decoded, max_iter, False


def modulate_bpsk(bits: List[int], snr_linear: float) -> np.ndarray:
    """BPSK调制 + AWGN"""
    x = np.array([1 if b == 1 else -1 for b in bits], dtype=np.float64)
    noise_std = 1.0 / np.sqrt(2 * snr_linear)
    noise = np.random.randn(len(x)) * noise_std
    return x + noise


if __name__ == '__main__':
    print('=== LDPC码 置信传播译码测试 ===')

    np.random.seed(42)

    # 简单规则LDPC码 (10, 20)
    H = np.array([
        [1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0],
        [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
        [0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0],
        [0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0],
        [0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,1],
        [1,0,0,0,0,1,0,0,0,0,1,0,0,1,0,0,0,0,1,0],
        [0,1,0,0,0,0,1,0,0,1,0,0,1,0,0,0,0,1,0,1],
    ], dtype=int)

    m, n_col = H.shape
    k = n_col - m
    print(f'LDPC码参数: n={n_col}, m={m}, rate={1-m/n_col:.2f}')

    info_bits = np.random.randint(0, 2, k).tolist()
    codeword = info_bits + [0] * m

    print(f'信息位长度: {k}, 码字长度: {n_col}')

    snr_db = 4.0
    snr_linear = 10 ** (snr_db / 10)

    recv = modulate_bpsk(codeword, snr_linear)
    llr_ch = llr_channel(recv, snr_linear)

    print(f'--- SNR = {snr_db} dB ---')

    decoded_bp, iters_bp, conv_bp = bp_decode(H, llr_ch, max_iter=50)
    syndrome_check = np.mod(H.dot(decoded_bp), 2).sum()
    n_errors_bp = sum(b1 != b2 for b1, b2 in zip(decoded_bp, codeword))
    print(f'BP译码: 收敛={conv_bp}, 迭代={iters_bp}, 校验方程错误={syndrome_check}')
    print(f'       比特错误={n_errors_bp}/{n_col}')

    decoded_ms, iters_ms, conv_ms = min_sum_decode(H, llr_ch, max_iter=50)
    syndrome_check_ms = np.mod(H.dot(decoded_ms), 2).sum()
    n_errors_ms = sum(b1 != b2 for b1, b2 in zip(decoded_ms, codeword))
    print(f'Min-Sum: 收敛={conv_ms}, 迭代={iters_ms}, 校验方程错误={syndrome_check_ms}')
    print(f'        比特错误={n_errors_ms}/{n_col}')

    print('--- 不同SNR下的LDPC译码性能 ---')
    for snr_test in [1.0, 2.0, 3.0, 4.0, 6.0, 8.0]:
        snr_lin = 10 ** (snr_test / 10)
        recv_t = modulate_bpsk(codeword, snr_lin)
        llr_t = llr_channel(recv_t, snr_lin)
        decoded_t, iters_t, _ = bp_decode(H, llr_t, max_iter=50)
        n_err = sum(b1 != b2 for b1, b2 in zip(decoded_t, codeword))
        ber = n_err / n_col
        bar = '#' * max(0, int(-np.log10(ber + 1e-10) * 3)) if ber > 0 else '########'
        print(f'  SNR={snr_test:.1f}dB: BER={ber:.4e} |{bar}')
