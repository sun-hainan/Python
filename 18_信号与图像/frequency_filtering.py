# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / frequency_filtering



本文件实现 frequency_filtering 相关的算法功能。

"""



import numpy as np

import math





class FrequencyFilter:

    """

    频率域滤波器基类

    """



    def __init__(self, shape):

        """

        初始化频率滤波器



        参数:

            shape: 图像/信号形状

        """

        self.shape = shape



    def create_filter(self):

        """创建滤波器"""

        raise NotImplementedError



    def apply(self, image):

        """

        应用滤波器



        参数:

            image: 输入图像

        返回:

            filtered: 滤波后图像

        """

        # 傅里叶变换

        F = np.fft.fft2(image)

        F_shift = np.fft.fftshift(F)



        # 创建滤波器

        H = self.create_filter()



        # 频域相乘

        G_shift = F_shift * H



        # 逆变换

        G = np.fft.ifftshift(G_shift)

        filtered = np.fft.ifft2(G)



        return np.real(filtered)





class IdealFilter(FrequencyFilter):

    """

    理想滤波器



    特点：锐截止，但有振铃效应。

    """



    def __init__(self, shape, cutoff, filter_type='lowpass'):

        """

        初始化理想滤波器



        参数:

            shape: 形状

            cutoff: 截止频率（像素）

            filter_type: 'lowpass', 'highpass', 'bandpass'

        """

        super().__init__(shape)

        self.cutoff = cutoff

        self.filter_type = filter_type



    def create_filter(self):

        """创建理想滤波器"""

        rows, cols = self.shape

        crow, ccol = rows // 2, cols // 2



        # 创建距离矩阵

        y, x = np.ogrid[:rows, :cols]

        distance = np.sqrt((y - crow)**2 + (x - ccol)**2)



        if self.filter_type == 'lowpass':

            H = (distance <= self.cutoff).astype(float)

        elif self.filter_type == 'highpass':

            H = (distance > self.cutoff).astype(float)

        elif self.filter_type == 'bandpass':

            if not hasattr(self, 'band_width'):

                self.band_width = self.cutoff * 0.2

            inner = distance >= (self.cutoff - self.band_width)

            outer = distance <= (self.cutoff + self.band_width)

            H = (inner & outer).astype(float)

        else:

            H = np.ones(self.shape)



        return H





class ButterworthFilter(FrequencyFilter):

    """

    Butterworth 频率域滤波器



    特点：平滑截止，过渡带介于理想和指数之间。

    """



    def __init__(self, shape, cutoff, order=2, filter_type='lowpass'):

        """

        初始化 Butterworth 滤波器



        参数:

            shape: 形状

            cutoff: 截止频率

            order: Butterworth 阶数

            filter_type: 类型

        """

        super().__init__(shape)

        self.cutoff = cutoff

        self.order = order

        self.filter_type = filter_type



    def create_filter(self):

        """创建 Butterworth 滤波器"""

        rows, cols = self.shape

        crow, ccol = rows // 2, cols // 2



        y, x = np.ogrid[:rows, :cols]

        distance = np.sqrt((y - crow)**2 + (x - ccol)**2)



        if self.filter_type == 'lowpass':

            H = 1 / (1 + (distance / self.cutoff) ** (2 * self.order))

        elif self.filter_type == 'highpass':

            H = 1 / (1 + (self.cutoff / (distance + 1e-8)) ** (2 * self.order))

        else:

            H = np.ones(self.shape)



        return H





class GaussianFilter(FrequencyFilter):

    """

    Gaussian 频率域滤波器



    特点：无振铃效应，最平滑。

    """



    def __init__(self, shape, sigma, filter_type='lowpass'):

        """

        初始化 Gaussian 滤波器



        参数:

            shape: 形状

            sigma: 高斯标准差

            filter_type: 类型

        """

        super().__init__(shape)

        self.sigma = sigma

        self.filter_type = filter_type



    def create_filter(self):

        """创建 Gaussian 滤波器"""

        rows, cols = self.shape

        crow, ccol = rows // 2, cols // 2



        y, x = np.ogrid[:rows, :cols]

        distance = np.sqrt((y - crow)**2 + (x - ccol)**2)



        if self.filter_type == 'lowpass':

            H = np.exp(-distance**2 / (2 * self.sigma**2))

        elif self.filter_type == 'highpass':

            H = 1 - np.exp(-distance**2 / (2 * self.sigma**2))

        else:

            H = np.ones(self.shape)



        return H





class BandRejectFilter(FrequencyFilter):

    """

    带阻滤波器（陷波滤波器）



    抑制特定频率范围。

    """



    def __init__(self, shape, center_freq, width):

        """

        初始化带阻滤波器



        参数:

            shape: 形状

            center_freq: 中心频率

            width: 阻带宽度

        """

        super().__init__(shape)

        self.center_freq = center_freq

        self.width = width



    def create_filter(self):

        """创建带阻滤波器"""

        rows, cols = self.shape

        crow, ccol = rows // 2, cols // 2



        y, x = np.ogrid[:rows, :cols]

        distance = np.sqrt((y - crow)**2 + (x - ccol)**2)



        # 陷波

        H = np.ones(self.shape)

        mask = (distance >= self.center_freq - self.width/2) & \

               (distance <= self.center_freq + self.width/2)

        H[mask] = 0



        return H





def create_grid_mask(shape, frequencies):

    """

    创建网格掩码（用于陷波滤波）



    参数:

        shape: 形状

        frequencies: 要抑制的频率点列表 [(f_row, f_col), ...]

    返回:

        mask: 掩码

    """

    rows, cols = shape

    crow, ccol = rows // 2, cols // 2



    y, x = np.ogrid[:rows, :cols]

    mask = np.ones(shape, dtype=bool)



    for fy, fx in frequencies:

        # 相对频率

        py, px = crow + fy, ccol + fx

        distance = np.sqrt((y - py)**2 + (x - px)**2)

        mask &= (distance > 3)  # 3 像素半径的陷波



    return mask





def frequency_filtering_1d(signal, filter_kernel):

    """

    一维频率域滤波



    参数:

        signal: 输入信号

        filter_kernel: 频率域滤波器（与 signal 同长度）

    返回:

        filtered: 滤波后信号

    """

    signal = np.array(signal, dtype=float)

    filter_kernel = np.array(filter_kernel, dtype=float)



    # FFT

    X = np.fft.fft(signal)

    H = np.fft.fft(filter_kernel)



    # 频域相乘

    Y = X * H



    # 逆 FFT

    return np.fft.ifft(Y).real





def design_lowpass_kernel(signal_length, cutoff_idx, filter_type='ideal'):

    """

    设计低通核



    参数:

        signal_length: 信号长度

        cutoff_idx: 截止索引

        filter_type: 'ideal', 'butterworth', 'gaussian'

    返回:

        kernel: 频域核

    """

    n = signal_length

    kernel = np.zeros(n)



    for k in range(n):

        if filter_type == 'ideal':

            kernel[k] = 1.0 if k <= cutoff_idx or k >= n - cutoff_idx else 0.0

        elif filter_type == 'butterworth':

            if cutoff_idx == 0:

                cutoff_idx = 1

            kernel[k] = 1.0 / (1.0 + (k / cutoff_idx) ** 8)

        elif filter_type == 'gaussian':

            if cutoff_idx == 0:

                cutoff_idx = 1

            sigma = cutoff_idx / 3

            kernel[k] = np.exp(-k**2 / (2 * sigma**2))



    return kernel





def remove_periodic_noise(image, noise_frequencies):

    """

    去除周期性噪声



    参数:

        image: 输入图像

        noise_frequencies: 噪声频率列表

    返回:

        cleaned: 去噪图像

    """

    rows, cols = image.shape

    crow, ccol = rows // 2, cols // 2



    # FFT

    F = np.fft.fft2(image)

    F_shift = np.fft.fftshift(F)



    # 创建陷波掩码

    mask = create_grid_mask((rows, cols), noise_frequencies)



    # 应用掩码

    F_filtered = F_shift * mask



    # 逆 FFT

    F_ifft = np.fft.ifftshift(F_filtered)

    cleaned = np.fft.ifft2(F_ifft)



    return np.real(cleaned)





def create_homomorphic_filter(shape, sigma_low=0.5, sigma_high=2.0):

    """

    创建同态滤波器（用于光照补偿）



    参数:

        shape: 形状

        sigma_low: 低频增益

        sigma_high: 高频增益

    返回:

        H: 滤波器

    """

    rows, cols = shape

    crow, ccol = rows // 2, cols // 2



    y, x = np.ogrid[:rows, :cols]

    distance = np.sqrt((y - crow)**2 + (x - ccol)**2)

    sigma = min(rows, cols) / 4



    H = sigma_low + (sigma_high - sigma_low) * \

        (1 - np.exp(-distance**2 / (2 * sigma**2)))



    return H





def homomorphic_filtering(image):

    """

    同态滤波（光照补偿 + 锐化）



    参数:

        image: 输入图像

    返回:

        result: 处理后图像

    """

    # 取对数

    log_image = np.log(image + 1e-10)



    # FFT

    F = np.fft.fft2(log_image)

    F_shift = np.fft.fftshift(F)



    # 滤波

    H = create_homomorphic_filter(image.shape)

    G_shift = F_shift * H



    # 逆 FFT

    G = np.fft.ifftshift(G_shift)

    g = np.fft.ifft2(G)



    # 指数变换

    result = np.exp(np.real(g))



    # 归一化

    result = (result - result.min()) / (result.max() - result.min())



    return result





if __name__ == "__main__":

    print("=== 频率域滤波测试 ===")



    # 创建测试图像

    print("\n1. 创建测试图像")

    rows, cols = 256, 256

    image = np.zeros((rows, cols))



    # 低频成分

    for i in range(rows):

        for j in range(cols):

            image[i, j] = 100 + 50 * np.sin(2*np.pi*10*i/rows) + \

                         30 * np.cos(2*np.pi*20*j/cols)



    # 添加高频噪声

    noise = np.random.randn(rows, cols) * 20

    noisy_image = image + noise



    print(f"图像尺寸: {image.shape}")

    print(f"原始图像均值: {np.mean(image):.2f}, 标准差: {np.std(image):.2f}")

    print(f"噪声图像均值: {np.mean(noisy_image):.2f}, 标准差: {np.std(noisy_image):.2f}")



    # 理想低通滤波

    print("\n2. 理想低通滤波")

    ideal_lp = IdealFilter((rows, cols), cutoff=30, filter_type='lowpass')

    filtered_ideal = ideal_lp.apply(noisy_image)

    print(f"滤波后均值: {np.mean(filtered_ideal):.2f}, 标准差: {np.std(filtered_ideal):.2f}")



    # Butterworth 低通

    print("\n3. Butterworth 低通滤波")

    butter_lp = ButterworthFilter((rows, cols), cutoff=30, order=2, filter_type='lowpass')

    filtered_butter = butter_lp.apply(noisy_image)

    print(f"滤波后均值: {np.mean(filtered_butter):.2f}, 标准差: {np.std(filtered_butter):.2f}")



    # Gaussian 低通

    print("\n4. Gaussian 低通滤波")

    gauss_lp = GaussianFilter((rows, cols), sigma=20, filter_type='lowpass')

    filtered_gauss = gauss_lp.apply(noisy_image)

    print(f"滤波后均值: {np.mean(filtered_gauss):.2f}, 标准差: {np.std(filtered_gauss):.2f}")



    # 高通滤波

    print("\n5. 高通滤波")

    gauss_hp = GaussianFilter((rows, cols), sigma=10, filter_type='highpass')

    filtered_hp = gauss_hp.apply(noisy_image)

    print(f"高通滤波后均值: {np.mean(filtered_hp):.2f}")



    # 带阻滤波

    print("\n6. 带阻滤波")

    band_reject = BandRejectFilter((rows, cols), center_freq=30, width=5)

    # filtered_br = band_reject.apply(noisy_image)



    # 频谱分析

    print("\n7. 频谱分析")

    F = np.fft.fft2(image)

    F_shift = np.fft.fftshift(F)

    magnitude = np.abs(F_shift)

    log_mag = np.log(magnitude + 1e-10)

    print(f"频谱范围: [{np.min(log_mag):.2f}, {np.max(log_mag):.2f}]")



    # 1D 频率滤波测试

    print("\n8. 1D 频率滤波")

    signal = np.sin(2*np.pi*10*np.linspace(0, 1, 256)) + \

             0.5*np.sin(2*np.pi*50*np.linspace(0, 1, 256))

    kernel = design_lowpass_kernel(256, cutoff=20, filter_type='butterworth')

    filtered_1d = frequency_filtering_1d(signal, kernel)

    print(f"原始信号 RMS: {np.sqrt(np.mean(signal**2)):.4f}")

    print(f"滤波后 RMS: {np.sqrt(np.mean(filtered_1d**2)):.4f}")



    # 同态滤波

    print("\n9. 同态滤波")

    test_image = np.random.rand(64, 64) * 0.5 + 0.5

    homomorphic = homomorphic_filtering(test_image)

    print(f"同态滤波后范围: [{np.min(homomorphic):.4f}, {np.max(homomorphic):.4f}]")



    print("\n频率域滤波测试完成!")

