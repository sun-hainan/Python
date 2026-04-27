# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / lifting_scheme



本文件实现 lifting_scheme 相关的算法功能。

"""



import numpy as np





class LiftingSchemeWavelet:

    """

    提升格式小波



    支持 Haar、db2 等常见小波的提升实现。

    """



    def __init__(self, name='haar'):

        """

        初始化提升格式小波



        参数:

            name: 小波名称

        """

        self.name = name

        if name == 'haar':

            self._init_haar()

        elif name == 'db2' or name == 'db4':

            self._init_daubechies(name)

        else:

            self._init_haar()



    def _init_haar(self):

        """Haar 小波的提升格式"""

        self.predict = lambda d, c: d - c

        self.update = lambda c, d: c + d / 2

        self.predict_inverse = lambda d, c: d + c

        self.update_inverse = lambda c, d: c - d / 2



    def _init_daubechies(self, name):

        """Daubechies 小波的提升格式"""

        # 简化实现

        self.predict = lambda d, c: d - 0.5 * c

        self.update = lambda c, d: c + 0.25 * d

        self.predict_inverse = lambda d, c: d + 0.5 * c

        self.update_inverse = lambda c, d: c - 0.25 * d



    def forward(self, signal):

        """

        前向提升格式变换



        参数:

            signal: 输入信号

        返回:

            c: 低频近似系数

            d: 高频细节系数

        """

        signal = np.array(signal, dtype=float)

        n = len(signal)



        # 分裂

        even = signal[::2]

        odd = signal[1::2]



        # 预测和更新

        d = np.zeros(len(even))

        c = even.copy()



        for i in range(len(even)):

            d[i] = self.predict(odd[i] if i < len(odd) else 0, c[i])

            if i < len(even) - 1:

                c[i + 1] = self.update(c[i], d[i])



        # 归一化

        c = c * np.sqrt(2)

        d = d * np.sqrt(2)



        return c, d



    def inverse(self, c, d):

        """

        逆提升格式变换



        参数:

            c: 低频近似系数

            d: 高频细节系数

        返回:

            signal: 重构信号

        """

        # 反归一化

        c = c / np.sqrt(2)

        d = d / np.sqrt(2)



        # 反更新

        even = c.copy()

        odd = np.zeros(len(even))



        for i in range(len(even)):

            if i < len(odd):

                odd[i] = self.predict_inverse(d[i], c[i])

            if i > 0:

                even[i] = self.update_inverse(even[i], d[i - 1])



        # 合并

        signal = np.zeros(len(even) * 2)

        signal[::2] = even

        signal[1::2] = odd



        return signal



    def forward_2d(self, image):

        """

        二维提升格式小波变换



        参数:

            image: 2D 图像

        返回:

            LL, LH, HL, HH: 子带

        """

        image = np.array(image, dtype=float)

        h, w = image.shape



        # 行变换

        rows = []

        for i in range(h):

            c, d = self.forward(image[i])

            rows.append(np.concatenate([c, d]))

        rows = np.array(rows)



        # 列变换

        cols = []

        for j in range(w):

            c, d = self.forward(rows[:, j])

            cols.append(np.concatenate([c, d]))

        cols = np.array(cols).T



        # 分离子带

        h2, w2 = h // 2, w // 2

        LL = cols[:h2, :w2]

        LH = cols[:h2, w2:]

        HL = cols[h2:, :w2]

        HH = cols[h2:, w2:]



        return LL, LH, HL, HH



    def inverse_2d(self, LL, LH, HL, HH):

        """

        二维逆提升格式小波变换



        参数:

            LL, LH, HL, HH: 子带

        返回:

            image: 重构图像

        """

        h2, w2 = LL.shape

        h, w = h2 * 2, w2 * 2



        # 合并子带

        top = np.concatenate([LL, LH], axis=1)

        bottom = np.concatenate([HL, HH], axis=1)

        merged = np.concatenate([top, bottom], axis=0)



        # 列逆变换

        cols = []

        for j in range(w):

            c = merged[:h2, j]

            d = merged[h2:, j]

            col = self.inverse(c, d)

            cols.append(col)

        cols = np.array(cols).T



        # 行逆变换

        rows = []

        for i in range(h):

            c = cols[i, :w2]

            d = cols[i, w2:]

            row = self.inverse(c, d)

            rows.append(row)



        return np.array(rows)





class LazyWaveletTransform:

    """

    Lazy 小波变换



    最简单的提升格式实现，直接在奇偶分裂后交换。

    """



    def forward(self, signal):

        """前向 Lazy 变换"""

        return signal[::2].copy(), signal[1::2].copy()



    def inverse(self, even, odd):

        """逆 Lazy 变换"""

        n = len(even) + len(odd)

        result = np.zeros(n)

        result[::2] = even

        result[1::2] = odd

        return result





class IntegerWavelet:

    """

    整数小波变换（使用提升格式）



    用于无损压缩和去噪。

    """



    def __init__(self):

        self.lifting = LiftingSchemeWavelet('haar')



    def forward(self, signal):

        """前向整数小波变换"""

        c, d = self.lifting.forward(signal)

        return np.round(c).astype(int), np.round(d).astype(int)



    def inverse(self, c, d):

        """逆整数小波变换"""

        c_float = c.astype(float)

        d_float = d.astype(float)

        return self.lifting.inverse(c_float, d_float)





def demo_wavelet_packet():

    """小波包分解演示"""

    print("=== 小波包分解演示 ===")



    signal = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])



    lifting = LiftingSchemeWavelet('haar')



    print(f"原始信号: {signal}")



    # 分解

    c, d = lifting.forward(signal)

    print(f"低频 c: {c}")

    print(f"高频 d: {d}")



    # 重构

    reconstructed = lifting.inverse(c, d)

    print(f"重构信号: {reconstructed}")

    print(f"重构误差: {np.max(np.abs(reconstructed - signal)):.10f}")



    # 整数变换

    int_signal = np.array([1, 2, 3, 4, 5, 6, 7, 8])

    print(f"\n整数信号: {int_signal}")

    int_wavelet = IntegerWavelet()

    c_int, d_int = int_wavelet.forward(int_signal)

    print(f"整数低频: {c_int}")

    print(f"整数高频: {d_int}")

    reconstructed_int = int_wavelet.inverse(c_int, d_int)

    print(f"整数重构: {reconstructed_int.astype(int)}")





if __name__ == "__main__":

    print("=== 提升格式小波变换测试 ===")



    # 测试信号

    print("\n1. 创建测试信号")

    n = 64

    t = np.arange(n) / n

    signal = np.sin(2 * np.pi * 5 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)

    print(f"信号长度: {len(signal)}")

    print(f"信号能量: {np.sum(signal**2):.4f}")



    # 提升格式变换

    print("\n2. 提升格式变换")

    lifting = LiftingSchemeWavelet('haar')

    c, d = lifting.forward(signal)

    print(f"低频系数长度: {len(c)}")

    print(f"高频系数长度: {len(d)}")

    print(f"c 能量: {np.sum(c**2):.4f}")

    print(f"d 能量: {np.sum(d**2):.4f}")

    print(f"总能量: {np.sum(c**2) + np.sum(d**2):.4f}")



    # 重构

    print("\n3. 信号重构")

    reconstructed = lifting.inverse(c, d)

    print(f"重构误差: {np.sqrt(np.mean((reconstructed - signal)**2)):.10f}")



    # 多层分解

    print("\n4. 多层分解")

    coeffs = []

    current = signal

    for level in range(3):

        c, d = lifting.forward(current)

        coeffs.append((c, d))

        current = c

        print(f"  Level {level+1}: c 长度={len(c)}, d 长度={len(d)}")



    # 2D 测试

    print("\n5. 2D 提升格式变换")

    image = np.random.rand(16, 16)

    image[4:12, 4:12] = 1.0  # 添加方块



    LL, LH, HL, HH = lifting.forward_2d(image)

    print(f"LL 形状: {LL.shape}")

    print(f"LH 形状: {LH.shape}")

    print(f"HL 形状: {HL.shape}")

    print(f"HH 形状: {HH.shape}")

    print(f"LL 能量: {np.sum(LL**2):.4f}")

    print(f"LH 能量: {np.sum(LH**2):.4f}")



    # 重构

    reconstructed_2d = lifting.inverse_2d(LL, LH, HL, HH)

    print(f"2D 重构误差: {np.sqrt(np.mean((reconstructed_2d - image)**2)):.10f}")



    # Lazy 小波

    print("\n6. Lazy 小波变换")

    lazy = LazyWaveletTransform()

    even, odd = lazy.forward(signal)

    merged = lazy.inverse(even, odd)

    print(f"偶采样长度: {len(even)}, 奇采样长度: {len(odd)}")

    print(f"Lazy 重构误差: {np.max(np.abs(merged - signal)):.10f}")



    # 整数小波

    print("\n7. 整数小波变换")

    int_signal = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])

    int_wavelet = IntegerWavelet()

    c_int, d_int = int_wavelet.forward(int_signal)

    reconstructed_int = int_wavelet.inverse(c_int, d_int)

    print(f"整数输入: {int_signal}")

    print(f"整数重构: {reconstructed_int.astype(int)}")

    print(f"无损: {np.array_equal(int_signal, reconstructed_int.astype(int))}")



    # 小波包演示

    print("\n8. 小波包分解")

    demo_wavelet_packet()



    print("\n提升格式小波变换测试完成!")

