# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / turbo_code_bcjr



本文件实现 turbo_code_bcjr 相关的算法功能。

"""



import numpy as np

from typing import Tuple, List, Dict

import math





class RSCEncoder:

    """递归系统卷积码（Recursive Systematic Convolutional）编码器"""

    def __init__(self, generator_poly: Tuple[int, int] = (5, 7)):

        self.g = generator_poly

        self.n_states = 4

        self.state = 0



    def _compute_parity(self, input_bit: int, state: int) -> int:

        s0 = (state >> 1) & 1

        s1 = state & 1

        return input_bit ^ s0 ^ s1



    def encode(self, info_bits: List[int]) -> Tuple[List[int], List[int]]:

        """编码信息位序列，返回（系统位，校验位）"""

        self.state = 0

        systematic_bits = []

        parity_bits = []



        for bit in info_bits:

            parity = self._compute_parity(bit, self.state)

            parity_bits.append(parity)

            systematic_bits.append(bit)

            feedback = bit ^ ((self.state >> 1) & 1) ^ (self.state & 1)

            self.state = ((self.state << 1) & 0b110) | (feedback & 1)



        return systematic_bits, parity_bits



    def reset(self):

        self.state = 0





def modulate_bpsk(bits: List[int], snr_linear: float = 10.0) -> np.ndarray:

    """BPSK调制 + AWGN信道"""

    x = np.array([1 if b == 1 else -1 for b in bits], dtype=np.float64)

    noise_std = 1.0 / np.sqrt(2 * snr_linear)

    noise = np.random.randn(len(x)) * noise_std

    return x + noise





def bcjr_decode(

    received_systematic: np.ndarray,

    received_parity: np.ndarray,

    prior_llr: np.ndarray,

    snr_linear: float,

    n_states: int = 4

) -> Tuple[np.ndarray, np.ndarray]:

    """

    BCJR算法（MAP译码）实现



    计算每个信息位的后验对数似然比（APP-LLR）



    参数:

        received_systematic: 接收的系统位（软值）

        received_parity: 接收的校验位（软值）

        prior_llr: 先验LLR（来自另一个译码器）

        snr_linear: SNR（线性值）

        n_states: 卷积码状态数



    返回:

        (app_llr, extrinsic_llr): 后验LLR和外部信息

    """

    n_bits = len(received_systematic)

    noise_var = 1.0 / (2 * snr_linear)



    gamma = np.zeros((n_bits, n_states, n_states))



    for k in range(n_bits):

        y_s = received_systematic[k]

        y_p = received_parity[k]

        prior_llr_k = prior_llr[k] if k < len(prior_llr) else 0.0

        p_u1 = 1.0 / (1.0 + np.exp(-prior_llr_k + 1e-10))

        p_u0 = 1.0 - p_u1



        for s_prev in range(n_states):

            u_k = (s_prev & 1)

            s_next = ((s_prev << 1) & (n_states - 1)) | u_k

            parity_bit = u_k ^ ((s_prev >> 1) & 1) ^ (s_prev & 1)

            expected_s = 1.0 if u_k == 1 else -1.0

            expected_p = 1.0 if parity_bit == 1 else -1.0

            llr_s = -(y_s - expected_s) ** 2 / (2 * noise_var)

            llr_p = -(y_p - expected_p) ** 2 / (2 * noise_var)



            if u_k == 1:

                gamma[k, s_prev, s_next] = np.exp(llr_s + llr_p) * p_u1

            else:

                gamma[k, s_prev, s_next] = np.exp(llr_s + llr_p) * p_u0



    alpha = np.zeros((n_bits + 1, n_states))

    alpha[0, 0] = 1.0

    for k in range(1, n_bits + 1):

        for s in range(n_states):

            alpha[k, s] = sum(alpha[k-1, s_prev] * gamma[k-1, s_prev, s]

                             for s_prev in range(n_states))

        alpha[k, :] = alpha[k, :] / (alpha[k, :].sum() + 1e-10)



    beta = np.zeros((n_bits + 1, n_states))

    beta[n_bits, 0] = 1.0

    for k in range(n_bits - 1, -1, -1):

        for s in range(n_states):

            beta[k, s] = sum(gamma[k, s, s_next] * beta[k+1, s_next]

                           for s_next in range(n_states))

        beta[k, :] = beta[k, :] / (beta[k, :].sum() + 1e-10)



    app_llr = np.zeros(n_bits)

    extrinsic_llr = np.zeros(n_bits)



    for k in range(n_bits):

        num1 = sum(alpha[k, s_prev] * gamma[k, s_prev, s_next] * beta[k+1, s_next]

                   for s_prev in range(n_states) for s_next in range(n_states)

                   if (s_prev & 1) == 1)

        num0 = sum(alpha[k, s_prev] * gamma[k, s_prev, s_next] * beta[k+1, s_next]

                   for s_prev in range(n_states) for s_next in range(n_states)

                   if (s_prev & 1) == 0)



        if num1 > 1e-10 and num0 > 1e-10:

            app_llr[k] = np.log(num1 / num0 + 1e-10)



        channel_llr = 2.0 * received_systematic[k] / noise_var

        extrinsic_llr[k] = app_llr[k] - prior_llr[k] - channel_llr



    return app_llr, extrinsic_llr





def turbo_iterative_decode(

    received_sys: np.ndarray,

    received_par1: np.ndarray,

    received_par2: np.ndarray,

    n_iter: int = 6,

    snr_linear: float = 10.0

) -> Tuple[np.ndarray, List[float]]:

    """

    Turbo码迭代译码



    交替使用两个BCJR译码器，每次迭代交换外部信息



    参数:

        received_sys: 接收的系统位

        received_par1: 来自编码器1的校验位

        received_par2: 来自编码器2的校验位（交织后）

        n_iter: 迭代次数

        snr_linear: SNR（线性值）



    返回:

        (hard_bits, llr_history): 硬判决结果和LLR变化历史

    """

    n_bits = len(received_sys)

    prior_llr = np.zeros(n_bits)

    llr_history = []



    interleaver = np.random.permutation(n_bits)

    deinterleaver = np.argsort(interleaver)



    sys_interleaved = received_sys[interleaver]

    par2_deint = received_par2[deinterleaver]



    for iteration in range(n_iter):

        app_llr_1, ext_llr_1 = bcjr_decode(

            received_sys, received_par1, prior_llr, snr_linear

        )

        ext_llr_1_interleaved = ext_llr_1[interleaver]

        app_llr_2, ext_llr_2 = bcjr_decode(

            sys_interleaved, par2_deint, ext_llr_1_interleaved, snr_linear

        )

        ext_llr_2_deinterleaved = ext_llr_2[deinterleaver]

        prior_llr = ext_llr_2_deinterleaved

        llr_history.append(np.mean(np.abs(app_llr_1)))



    hard_bits = (app_llr_1 > 0).astype(int)

    return hard_bits, llr_history





if __name__ == '__main__':

    print('=== Turbo码 MAP/BCJR算法测试 ===')



    np.random.seed(42)



    n_bits = 100

    info_bits = np.random.randint(0, 2, n_bits).tolist()



    encoder = RSCEncoder()

    sys_bits, parity_bits = encoder.encode(info_bits)



    print(f'信息位长度: {n_bits}')

    print(f'编码后长度: {len(sys_bits)} 系统位 + {len(parity_bits)} 校验位')



    snr_db = 2.0

    snr_linear = 10 ** (snr_db / 10)



    recv_sys = modulate_bpsk(sys_bits, snr_linear)

    recv_par1 = modulate_bpsk(parity_bits, snr_linear)

    recv_par2 = modulate_bpsk(parity_bits, snr_linear)



    print(f'--- SNR = {snr_db} dB ---')

    hard_bits, llr_hist = turbo_iterative_decode(

        recv_sys, recv_par1, recv_par2,

        n_iter=6, snr_linear=snr_linear

    )



    n_errors = sum(b1 != b2 for b1, b2 in zip(hard_bits, info_bits))

    print(f'错误位数: {n_errors}/{n_bits}')

    print(f'误码率: {n_errors/n_bits:.4f}')

    print(f'LLR收敛: {[f"{x:.3f}" for x in llr_hist]}')



    print('--- 不同SNR下的Turbo译码性能 ---')

    for snr_db_test in [0.5, 1.0, 2.0, 3.0, 5.0]:

        snr_lin = 10 ** (snr_db_test / 10)

        recv_sys_t = modulate_bpsk(sys_bits, snr_lin)

        recv_par1_t = modulate_bpsk(parity_bits, snr_lin)

        recv_par2_t = modulate_bpsk(parity_bits, snr_lin)



        hard_t, _ = turbo_iterative_decode(

            recv_sys_t, recv_par1_t, recv_par2_t,

            n_iter=6, snr_linear=snr_lin

        )

        n_err = sum(b1 != b2 for b1, b2 in zip(hard_t, info_bits))

        ber = n_err / n_bits

        bar = '#' * max(0, int(-np.log10(ber + 1e-10) * 3)) if ber > 0 else '########'

        print(f'  SNR={snr_db_test:.1f}dB: BER={ber:.4e} |{bar}')

