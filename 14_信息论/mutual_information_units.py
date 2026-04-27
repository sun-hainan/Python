# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / mutual_information_units



本文件实现 mutual_information_units 相关的算法功能。

"""



import numpy as np

from typing import Dict, Tuple

import math





def bits_to_nats(bits: float) -> float:

    """将bit转换为nat（乘以ln2的倒数，即乘以log2(e)）"""

    return bits * math.log(2)





def nats_to_bits(nats: float) -> float:

    """将nat转换为bit（乘以ln2）"""

    return nats * math.log(2)





def bits_to_bans(bits: float) -> float:

    """将bit转换为ban（乘以log2(10)）"""

    return bits * math.log10(2)





def bans_to_bits(bans: float) -> float:

    """将ban转换为bit（乘以log10(2)的倒数）"""

    return bans / math.log10(2)





def convert_entropy(value: float, from_unit: str, to_unit: str) -> float:

    """熵值单位转换"""

    if from_unit == to_unit:

        return value

    if from_unit == 'bit':

        bits = value

    elif from_unit == 'nat':

        bits = nats_to_bits(value)

    elif from_unit == 'ban':

        bits = bans_to_bits(value)

    else:

        raise ValueError(f'Unknown unit: {from_unit}')



    if to_unit == 'bit':

        return bits

    elif to_unit == 'nat':

        return bits_to_nats(bits)

    elif to_unit == 'ban':

        return bits_to_bans(bits)

    else:

        raise ValueError(f'Unknown unit: {to_unit}')





def boltzmann_entropy(k_B: float, Omega: float) -> float:

    """玻尔兹曼熵公式：S = k_B * ln(Omega)"""

    return k_B * math.log(Omega)





def spectral_efficiency(bits_per_second: float, bandwidth_hz: float) -> float:

    """频谱效率 eta = R / B  bits/s/Hz"""

    return bits_per_second / bandwidth_hz





def mutual_information_normalized(H_X: float, H_Y: float, I_XY: float) -> Tuple[float, float, float]:

    """归一化互信息分析"""

    I_over_HX = I_XY / H_X if H_X > 1e-10 else 0.0

    I_over_HY = I_XY / H_Y if H_Y > 1e-10 else 0.0

    H_XY = H_X + H_Y - I_XY

    I_over_HXY = I_XY / H_XY if H_XY > 1e-10 else 0.0

    return I_over_HX, I_over_HY, I_over_HXY





def channel_capacity_dimensions(bandwidth_hz: float, snr_linear: float) -> Dict[str, float]:

    """香农容量公式的量纲分析 C = B * log2(1 + SNR) bits/s"""

    C_bps = bandwidth_hz * math.log2(1 + snr_linear)

    C_per_symbol = math.log2(1 + snr_linear)

    return {

        'capacity_bps': C_bps,

        'capacity_per_use': C_per_symbol,

        'snr_db': 10 * math.log10(snr_linear),

        'bandwidth_hz': bandwidth_hz,

    }





def data_compression_ratio(H_X: float, code_len_efficient: float) -> Tuple[float, float]:

    """数据压缩比分析"""

    compression_ratio = code_len_efficient / H_X if H_X > 1e-10 else float('inf')

    efficiency = H_X / code_len_efficient if code_len_efficient > 1e-10 else 0.0

    return compression_ratio, efficiency





def kl_divergence_units(P: np.ndarray, Q: np.ndarray, unit: str = 'bit') -> float:

    """计算KL散度 D(P||Q) = sum P_i * log(P_i / Q_i) 并转换单位"""

    D_nat = 0.0

    for p_i, q_i in zip(P, Q):

        if p_i > 1e-10 and q_i > 1e-10:

            D_nat += p_i * math.log(p_i / q_i)



    if unit == 'nat':

        return D_nat

    elif unit == 'bit':

        return D_nat / math.log(2)

    elif unit == 'ban':

        return D_nat / math.log(10)

    else:

        return D_nat





if __name__ == '__main__':

    print('=== 互信息量纲分析测试 ===')



    print('--- 测试1: 熵单位转换 ---')

    bits_value = 8.0

    print(f'{bits_value} bit = {bits_to_nats(bits_value):.4f} nat = {bits_to_bans(bits_value):.4f} ban')

    print(f'{bits_value} bit = {bits_value * math.log(2):.4f} nats (check)')

    print(f'{bits_value} bit = {bits_value * math.log10(2):.4f} bans (check)')



    print('--- 测试2: 玻尔兹曼熵 ---')

    k_B = 1.38e-23

    for Omega in [1e23, 1e24, 1e25, 1e26]:

        S = boltzmann_entropy(k_B, Omega)

        print(f'  Omega={Omega:.0e}: S={S:.4e} J/K = {S/1e-23:.4e} k_B')



    print('--- 测试3: 香农容量量纲分析 ---')

    B = 1e6

    for snr_db in [0, 3, 6, 10, 20]:

        snr_lin = 10 ** (snr_db / 10)

        result = channel_capacity_dimensions(B, snr_lin)

        print(f'  SNR={snr_db}dB: C={result["capacity_bps"]/1e6:.2f} Mbps, 每符号={result["capacity_per_use"]:.2f} bits')



    print('--- 测试4: 归一化互信息 ---')

    test_cases = [

        (4.0, 4.0, 2.0),

        (4.0, 4.0, 4.0),

        (4.0, 4.0, 0.0),

        (3.0, 5.0, 2.0),

    ]

    print(f'  {"H(X)":>6} {"H(Y)":>6} {"I(X;Y)":>8} {"I/H(X)":>8} {"I/H(Y)":>8} {"I/H(X,Y)":>10}')

    print('  ' + '-' * 55)

    for H_X, H_Y, I_XY in test_cases:

        i_hx, i_hy, i_hxy = mutual_information_normalized(H_X, H_Y, I_XY)

        print(f'  {H_X:6.2f} {H_Y:6.2f} {I_XY:8.4f} {i_hx:8.4f} {i_hy:8.4f} {i_hxy:10.4f}')



    print('--- 测试5: KL散度单位 ---')

    P = np.array([0.4, 0.3, 0.2, 0.1])

    Q = np.array([0.25, 0.25, 0.25, 0.25])

    D_bit = kl_divergence_units(P, Q, 'bit')

    D_nat = kl_divergence_units(P, Q, 'nat')

    D_ban = kl_divergence_units(P, Q, 'ban')

    print(f'  D(P||Q) = {D_bit:.4f} bits = {D_nat:.4f} nats = {D_ban:.4f} bans')

    print(f'  验证: {D_nat:.4f} / {D_bit:.4f} = {D_nat/D_bit:.4f} ~= ln(2)={math.log(2):.4f}')



    print('--- 测试6: 数据压缩效率分析 ---')

    for H_X in [1.0, 2.0, 3.0, 4.0]:

        for code_len in [1.2, 1.5, 2.0, 3.0]:

            ratio, eff = data_compression_ratio(H_X, code_len)

            bar = '#' * int(eff * 20)

            print(f'  H={H_X:.1f}, L={code_len:.1f}: 压缩比={ratio:.3f}, 效率={eff:.3f} |{bar}')

