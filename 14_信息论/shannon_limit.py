# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / shannon_limit



本文件实现 shannon_limit 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Dict

import math





def snr_db_to_linear(snr_db: float) -> float:

    """将信噪比从dB转换为线性值 SNR_linear = 10^(SNR_dB / 10)"""

    return 10 ** (snr_db / 10.0)





def shannon_capacity_awgn(bandwidth_hz: float, snr_db: float) -> float:

    """

    计算AWGN（加性高斯白噪声）信道的香农容量



    公式: C = B * log2(1 + SNR)



    参数:

        bandwidth_hz: 信道带宽 B (Hz)

        snr_db: 信噪比（dB）



    返回:

        C: 信道容量 (bits/second)

    """

    snr = snr_db_to_linear(snr_db)

    C_bps = bandwidth_hz * math.log2(1 + snr)

    return C_bps





def spectral_efficiency_limit(snr_db: float) -> float:

    """

    计算AWGN信道下单位带宽的容量极限（频谱效率）



    eta = log2(1 + SNR_linear)  bits/s/Hz



    参数:

        snr_db: 信噪比（dB）



    返回:

        频谱效率极限 (bits/s/Hz)

    """

    snr = snr_db_to_linear(snr_db)

    return math.log2(1 + snr)





def required_snr_for_efficiency(efficiency_bps_hz: float) -> float:

    """

    计算达到指定频谱效率所需的最小SNR（反向香农公式）



    由 eta = log2(1+SNR) 反解：SNR = 2^eta - 1



    参数:

        efficiency_bps_hz: 目标频谱效率 (bits/s/Hz)



    返回:

        所需最小SNR（线性值）

    """

    return (2 ** efficiency_bps_hz) - 1





def required_snr_db_for_efficiency(efficiency_bps_hz: float) -> float:

    """计算达到指定频谱效率所需的最小SNR（dB）"""

    snr_linear = required_snr_for_efficiency(efficiency_bps_hz)

    return 10 * math.log10(snr_linear + 1e-10)





def coding_gain_over_shannon(actual_snr_db: float, target_efficiency: float) -> Tuple[float, float]:

    """

    计算实际SNR与香农极限的差距



    参数:

        actual_snr_db: 实际信噪比（dB）

        target_efficiency: 目标频谱效率 (bits/s/Hz)



    返回:

        (gap_db, gap_ratio): gap_db为与极限的dB差距，gap_ratio为线性比值

    """

    snr_actual = snr_db_to_linear(actual_snr_db)

    snr_required = required_snr_for_efficiency(target_efficiency)

    gap_ratio = snr_actual / (snr_required + 1e-10)

    gap_db = 10 * math.log10(gap_ratio + 1e-10)

    return gap_db, gap_ratio





def Q_function(x: float) -> float:

    """Q函数：标准正态分布的尾概率 Q(x) = 0.5 * erfc(x/sqrt(2))"""

    return 0.5 * math.erfc(x / np.sqrt(2))





def ber_awgn_approximation(snr_db: float, modulation: str = 'bpsk') -> float:

    """

    近似计算AWGN信道下不同调制的理论误码率



    参数:

        snr_db: 信噪比（dB）

        modulation: 调制方式 ('bpsk', 'qpsk', '16qam', '64qam')



    返回:

        理论误码率（近似值）

    """

    snr = snr_db_to_linear(snr_db)

    bits_per_symbol = {'bpsk': 1, 'qpsk': 2, '16qam': 4, '64qam': 6}

    m = bits_per_symbol.get(modulation, 1)

    snr_per_bit = snr / m



    if modulation == 'bpsk':

        Q_arg = np.sqrt(2 * snr_per_bit)

        ber = 0.5 * math.erfc(Q_arg / np.sqrt(2))

    elif modulation == 'qpsk':

        Q_arg = np.sqrt(snr_per_bit)

        ber = 0.5 * math.erfc(Q_arg / np.sqrt(2))

    elif modulation == '16qam':

        Q_arg = np.sqrt(3 * snr_per_bit / 15)

        ber = 3/4 * 0.5 * math.erfc(Q_arg / np.sqrt(2))

    elif modulation == '64qam':

        Q_arg = np.sqrt(snr_per_bit / 21)

        ber = 7/12 * 0.5 * math.erfc(Q_arg / np.sqrt(2))

    else:

        ber = 0.5 * math.erfc(np.sqrt(snr_per_bit) / np.sqrt(2))



    return max(1e-15, min(1.0, ber))





if __name__ == '__main__':

    print('=== 香农极限测试 ===')



    print('--- 测试1: 香农容量（AWGN信道）---')

    bandwidth = 1e6  # 1 MHz

    for snr_db in [0, 3, 6, 10, 20, 30]:

        C = shannon_capacity_awgn(bandwidth, snr_db)

        eta = spectral_efficiency_limit(snr_db)

        print(f'  SNR={snr_db:3d}dB: C={C/1e6:6.2f} Mbps  频谱效率={eta:.2f} bits/s/Hz')



    print('--- 测试2: 频谱效率 vs 所需最小SNR ---')

    print(f'  {"效率(b/s/Hz)":>15}  {"所需SNR(dB)":>12}  {"所需SNR(线性)":>14}')

    print('  ' + '-' * 45)

    for eta in [1, 2, 3, 4, 5, 6, 8, 10]:

        snr_req = required_snr_db_for_efficiency(eta)

        snr_lin = required_snr_for_efficiency(eta)

        print(f'  {eta:15.1f}  {snr_req:12.2f} dB  {snr_lin:14.4f}')



    print('--- 测试3: 香农极限曲线（频谱效率 vs SNR）---')

    print(f'  {"SNR(dB)":>10}  {"eta极限(b/s/Hz)":>15}  {"可用SNR距离极限":>18}')

    print('  ' + '-' * 50)

    for snr_db in range(-5, 36, 5):

        eta = spectral_efficiency_limit(snr_db)

        gap_db, _ = coding_gain_over_shannon(snr_db, eta)

        bar = '#' * int(eta * 3)

        print(f'  {snr_db:10d}  {eta:15.4f}  {gap_db:+.2f} dB |{bar}')



    print('--- 测试4: 不同调制方案的理论误码率（AWGN）---')

    print(f'  {"SNR(dB)":>10}  {"BPSK BER":>12}  {"QPSK BER":>12}  {"16QAM BER":>12}')

    print('  ' + '-' * 55)

    for snr_db in [2, 4, 6, 8, 10, 12]:

        ber_bpsk = ber_awgn_approximation(snr_db, 'bpsk')

        ber_qpsk = ber_awgn_approximation(snr_db, 'qpsk')

        ber_16qam = ber_awgn_approximation(snr_db, '16qam')

        print(f'  {snr_db:10d}  {ber_bpsk:12.2e}  {ber_qpsk:12.2e}  {ber_16qam:12.2e}')

