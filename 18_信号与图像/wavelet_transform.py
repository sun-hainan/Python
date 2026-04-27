# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / wavelet_transform



本文件实现 wavelet_transform 相关的算法功能。

"""



import numpy as np

import math





class Wavelet:

    """小波基类"""



    def __init__(self, name='haar'):

        self.name = name

        if name == 'haar':

            self._init_haar()

        elif name.startswith('db'):

            n = int(name[2:])

            self._init_daubechies(n)

        else:

            self._init_haar()



    def _init_haar(self):

        """Haar 小波"""

        self.decompose_low = np.array([1/np.sqrt(2), 1/np.sqrt(2)])

        self.decompose_high = np.array([-1/np.sqrt(2), 1/np.sqrt(2)])

        self.reconstruct_low = np.array([1/np.sqrt(2), -1/np.sqrt(2)])

        self.reconstruct_high = np.array([1/np.sqrt(2), 1/np.sqrt(2)])



    def _init_daubechies(self, n):

        """Daubechies 小波（简化）"""

        # 简化为 n/2 长度的低通滤波器系数

        # 实际需要查表或计算

        length = n

        self.decompose_low = np.ones(length) / np.sqrt(n)

        self.decompose_high = np.array([(-1)**i for i in range(length)]) / np.sqrt(n)

        self.reconstruct_low = self.decompose_low[::-1] * (1 if n % 4 < 2 else -1)

        self.reconstruct_high = self.decompose_high[::-1] * (-1 if n % 4 < 2 else 1)





class DWT:

    """

    离散小波变换（Discrete Wavelet Transform）



    使用指定小波基进行一维和二维 DWT。

    """



    def __init__(self, wavelet='haar'):

        """

        初始化 DWT



        参数:

            wavelet: 小波基名称 ('haar', 'db4', etc.)

        """

        self.wavelet = Wavelet(wavelet)



    def dwt_1d(self, signal):

        """

        一维离散小波变换



        参数:

            signal: 输入信号

        返回:

            cA: 低频近似系数

            cD: 高频细节系数

        """

        signal = np.array(signal, dtype=float)

        n = len(signal)



        # 确保长度是 2 的幂

        if n & (n - 1):

            n = 2 ** int(np.ceil(np.log2(n)))

            signal = np.pad(signal, (0, n - len(signal)))



        low = self.wavelet.decompose_low

        high = self.wavelet.decompose_high



        # 卷积下采样

        cA = np.convolve(signal, low, mode='valid')[::2]

        cD = np.convolve(signal, high, mode='valid')[::2]



        return cA, cD



    def idwt_1d(self, cA, cD):

        """

        一维离散小波逆变换



        参数:

            cA: 低频近似系数

            cD: 高频细节系数

        返回:

            signal: 重构信号

        """

        low = self.wavelet.reconstruct_low

        high = self.wavelet.reconstruct_high



        # 上采样卷积

        up_cA = np.zeros(len(cA) * 2)

        up_cA[::2] = cA

        up_cD = np.zeros(len(cD) * 2)

        up_cD[::2] = cD



        a = np.convolve(up_cA, low, mode='valid')

        d = np.convolve(up_cD, high, mode='valid')



        return a + d



    def dwt_2d(self, image, level=1):

        """

        二维离散小波变换



        参数:

            image: 2D 图像

            level: 分解层数

        返回:

            coeffs: 小波系数字典

        """

        image = np.array(image, dtype=float)

        h, w = image.shape

        coeffs = {'approx': [], 'horizontal': [], 'vertical': [], 'diagonal': []}



        current = image.copy()



        for l in range(level):

            # 行变换

            rows = current.shape[0]

            row_coeffs = []

            for i in range(rows):

                cA, cD = self.dwt_1d(current[i])

                row_coeffs.append(np.concatenate([cA, cD]))

            current = np.array(row_coeffs)



            # 列变换

            cols = current.shape[1]

            col_coeffs = []

            for j in range(cols):

                cA, cD = self.dwt_1d(current[:, j])

                col_coeffs.append(np.concatenate([cA, cD]))

            current = np.array(col_coeffs).T



            # 分离各子带

            h2, w2 = current.shape[0] // 2, current.shape[1] // 2

            coeffs['approx'].append(current[:h2, :w2])

            coeffs['horizontal'].append(current[:h2, w2:])

            coeffs['vertical'].append(current[h2:, :w2])

            coeffs['diagonal'].append(current[h2:, w2:])



        return coeffs



    def idwt_2d(self, coeffs):

        """

        二维离散小波逆变换



        参数:

            coeffs: 小波系数

        返回:

            image: 重构图像

        """

        level = len(coeffs['approx'])



        # 从最低层开始重构

        current = coeffs['approx'][-1]



        for l in range(level - 1, -1, -1):

            h2, w2 = coeffs['approx'][l].shape[0], coeffs['approx'][l].shape[1]



            # 合并子带

            top = np.concatenate([coeffs['approx'][l], coeffs['horizontal'][l]], axis=1)

            bottom = np.concatenate([coeffs['vertical'][l], coeffs['diagonal'][l]], axis=1)

            current = np.concatenate([top, bottom], axis=0)



            # 列逆变换

            rows = []

            for j in range(current.shape[1]):

                col = current[:, j]

                cA = col[:len(col)//2]

                cD = col[len(col)//2:]

                row = self.idwt_1d(cA, cD)

                rows.append(row)

            current = np.array(rows).T



            # 行逆变换

            cols = []

            for i in range(current.shape[0]):

                row = self.idwt_1d(current[i, :len(current[i])//2],

                                   current[i, len(current[i])//2:])

                cols.append(row)

            current = np.array(cols)



        return current



    def denoise(self, signal, threshold_factor=0.5):

        """

        小波去噪



        参数:

            signal: 输入信号

            threshold_factor: 阈值因子（相对于最大系数）

        返回:

            denoised: 去噪信号

        """

        cA, cD = self.dwt_1d(signal)



        # 软阈值

        threshold = threshold_factor * np.max(np.abs(cD))

        cD_thresh = np.sign(cD) * np.maximum(np.abs(cD) - threshold, 0)



        return self.idwt_1d(cA, cD_thresh)



    def compress(self, signal, keep_ratio=0.5):

        """

        小波压缩（简单版本）



        参数:

            signal: 输入信号

            keep_ratio: 保留系数比例

        返回:

            compressed: 压缩后信号

            retained: 保留的系数索引

        """

        cA, cD = self.dwt_1d(signal)



        # 保留能量最大的系数

        all_coeffs = np.concatenate([cA, cD])

        threshold = np.percentile(np.abs(all_coeffs), (1 - keep_ratio) * 100)



        retained_cA = np.where(np.abs(cA) >= threshold)[0]

        retained_cD = np.where(np.abs(cD) >= threshold)[0]



        return (cA[retained_cA], retained_cA), (cD[retained_cD], retained_cD)





class CWT:

    """

    连续小波变换（Continuous Wavelet Transform）



    CWT 提供连续的时频分析。

    """



    def __init__(self, wavelet='mexican_hat'):

        self.wavelet = wavelet



    def mexican_hat(self, t, sigma=1.0):

        """

        Mexican Hat（小波）函数



        ψ(t) = (2/√3σ) * π^(-1/4) * (1 - t²/σ²) * exp(-t²/(2σ²))

        """

        return (2 / (np.sqrt(3 * sigma) * np.pi**0.25)) * \

               (1 - (t / sigma)**2) * np.exp(-t**2 / (2 * sigma**2))



    def morlet(self, t, omega0=5.0):

        """

        Morlet 小波



        ψ(t) = π^(-1/4) * exp(iω₀t) * exp(-t²/2)

        """

        return np.pi**(-0.25) * np.exp(1j * omega0 * t) * np.exp(-t**2 / 2)



    def cwt_1d(self, signal, scales, dt=1.0):

        """

        一维连续小波变换



        参数:

            signal: 输入信号

            scales: 尺度序列

            dt: 采样间隔

        返回:

            coeffs: 小波系数矩阵 (len(scales), len(signal))

        """

        n = len(signal)

        coeffs = np.zeros((len(scales), n), dtype=complex)



        for i, scale in enumerate(scales):

            # 核长度

            M = int(10 * scale)

            t = np.arange(-M, M + 1) * dt



            if self.wavelet == 'mexican_hat':

                psi = self.mexican_hat(t / scale) / scale

            else:

                psi = np.real(self.morlet(t / scale)) / scale



            # 卷积

            coeffs[i] = np.convolve(signal, psi, mode='same')



        return coeffs



    def get_frequencies(self, scales, dt=1.0, central_freq=1.0):

        """

        将尺度转换为频率



        参数:

            scales: 尺度序列

            dt: 采样间隔

            central_freq: 小波中心频率

        返回:

            frequencies: 频率序列

        """

        return central_freq / (scales * dt)





def haar_wavelet_1d(signal, n_levels=1):

    """

    Haar 小波变换（简化实现）



    参数:

        signal: 输入信号

        n_levels: 分解层数

    返回:

        details: 细节系数列表

        approximation: 近似系数

    """

    signal = np.array(signal, dtype=float)

    details = []

    current = signal



    for level in range(n_levels):

        n = len(current)

        if n < 2:

            break



        # 确保偶数长度

        if n % 2:

            current = current[:-1]



        # 低通 (平均) 和 高通 (细节)

        even = current[::2]

        odd = current[1::2]



        approximation = (even + odd) / np.sqrt(2)

        detail = (even - odd) / np.sqrt(2)



        details.append(detail)

        current = approximation



    return details, current





def inverse_haar_wavelet(details, approximation):

    """

    Haar 小波逆变换



    参数:

        details: 细节系数列表（从低到高）

        approximation: 最低层近似系数

    返回:

        signal: 重构信号

    """

    current = approximation



    for detail in reversed(details):

        even = (current + detail) / np.sqrt(2)

        odd = (current - detail) / np.sqrt(2)

        current = np.zeros(len(even) * 2)

        current[::2] = even

        current[1::2] = odd



    return current





if __name__ == "__main__":

    print("=== 小波变换测试 ===")



    # 创建测试信号

    print("\n1. 创建测试信号")

    t = np.linspace(0, 1, 256)

    signal = np.sin(2 * np.pi * 10 * t)  # 10 Hz 正弦波

    # 添加噪声

    noise = np.random.randn(256) * 0.3

    noisy_signal = signal + noise

    print(f"信号长度: {len(signal)}")

    print(f"SNR: {10 * np.log10(np.var(signal) / np.var(noise)):.2f} dB")



    # Haar 小波分解

    print("\n2. Haar 小波分解")

    details, approx = haar_wavelet_1d(noisy_signal, n_levels=3)

    print(f"分解层数: {len(details)}")

    print(f"近似系数长度: {len(approx)}")

    for i, d in enumerate(details):

        print(f"  细节 {i+1} 长度: {len(d)}, 能量: {np.sum(d**2):.4f}")



    # 重构

    print("\n3. Haar 小波重构")

    reconstructed = inverse_haar_wavelet(details, approx)

    print(f"重构信号长度: {len(reconstructed)}")

    print(f"重构误差: {np.sqrt(np.mean((reconstructed - noisy_signal)**2)):.4f}")



    # DWT 测试

    print("\n4. DWT 测试")

    dwt = DWT('haar')

    cA, cD = dwt.dwt_1d(noisy_signal)

    print(f"cA 长度: {len(cA)}, cD 长度: {len(cD)}")



    # 去噪

    print("\n5. 小波去噪")

    denoised = dwt.denoise(noisy_signal, threshold_factor=0.3)

    snr_after = 10 * np.log10(np.var(signal) / np.var(denoised - signal))

    print(f"去噪后 SNR: {snr_after:.2f} dB")



    # 2D DWT 测试

    print("\n6. 2D DWT 测试")

    image = np.random.rand(32, 32)

    # 添加边缘

    image[8:24, 8:24] += 1.0



    dwt2d = DWT('haar')

    coeffs = dwt2d.dwt_2d(image, level=2)

    print(f"分解层数: 2")

    for i, approx in enumerate(coeffs['approx']):

        print(f"  Level {i+1} approx 形状: {approx.shape}")

    print(f"  Level 1 horizontal 形状: {coeffs['horizontal'][0].shape}")



    # 重构

    print("\n7. 2D 重构")

    reconstructed_2d = dwt2d.idwt_2d(coeffs)

    print(f"重构图像形状: {reconstructed_2d.shape}")

    print(f"重构误差: {np.sqrt(np.mean((reconstructed_2d - image)**2)):.4f}")



    # CWT 测试

    print("\n8. 连续小波变换测试")

    cwt = CWT('mexican_hat')

    scales = np.linspace(1, 32, 32)

    cwt_coeffs = cwt.cwt_1d(signal[:64], scales, dt=1/256)

    print(f"CWT 系数形状: {cwt_coeffs.shape}")



    freqs = cwt.get_frequencies(scales, dt=1/256)

    print(f"频率范围: [{freqs[-1]:.2f}, {freqs[0]:.2f}] Hz")



    # 压缩测试

    print("\n9. 小波压缩测试")

    keep_ratio = 0.3

    (cA_ret, idx_A), (cD_ret, idx_D) = dwt.compress(signal, keep_ratio=keep_ratio)

    n_coeffs = len(idx_A) + len(idx_D)

    compression_ratio = len(signal) / n_coeffs

    print(f"原始系数: {len(signal)}, 保留: {n_coeffs}")

    print(f"压缩比: {compression_ratio:.2f}x")



    print("\n小波变换测试完成!")

