# -*- coding: utf-8 -*-
"""
算法实现：压缩感知 / compressed_sensing

本文件实现 compressed_sensing 相关的算法功能。
"""

import numpy as np  # numpy: 数值计算库，提供数组和矩阵运算
from typing import Optional, Tuple  # typing: 类型提示支持
from scipy import sparse  # scipy: 科学计算工具库
from scipy.sparse import issparse  # issparse: 稀疏矩阵检测函数


class SignalModel:
    """
    信号模型类 (Signal Model Class)
    
    封装压缩感知中的信号模型，支持稀疏信号生成、
    字典构造以及测量过程模拟。
    
    属性:
        n: 信号维度 (signal dimension)
        k: 稀疏度 (sparsity level)
        dictionary: 稀疏表示字典 (sparse representation dictionary)
        measurement_matrix: 测量矩阵 (measurement matrix)
    """
    
    def __init__(self, n, k, m):
        """
        初始化信号模型 (Initialize Signal Model)
        
        参数:
            n: 信号维度 (dimension of the signal space)
            k: 目标稀疏度 (target sparsity level)
            m: 测量数量 (number of measurements, m << n)
        """
        self.n = n  # 信号维度 (signal dimension)
        self.k = k  # 稀疏度 (sparsity level)
        self.m = m  # 测量数量 (number of measurements)
        self.dictionary = None  # 字典矩阵 (dictionary matrix)
        self.measurement_matrix = None  # 测量矩阵 (measurement matrix)
        self._initialize_matrices()  # 初始化矩阵 (initialize matrices)
    
    def _initialize_matrices(self):
        """
        初始化字典矩阵和测量矩阵 (Initialize Dictionary and Measurement Matrices)
        
        使用高斯随机矩阵作为测量矩阵，FFT矩阵作为字典。
        这种组合在实践中表现出良好的重建性能。
        """
        # 高斯随机测量矩阵: 每个元素服从 N(0, 1/m) 分布
        # Gaussian random measurement matrix: entries ~ N(0, 1/m)
        self.measurement_matrix = np.random.randn(self.m, self.n) / np.sqrt(self.m)
        
        # 构造基于离散余弦变换(DCT)的字典矩阵
        # Construct dictionary based on Discrete Cosine Transform (DCT)
        dct_matrix = self._construct_dct_dictionary()
        
        # 对字典进行归一化处理，使每列具有单位范数
        # Normalize dictionary columns to unit norm
        norms = np.linalg.norm(dct_matrix, axis=0)  # 计算每列的 ℓ₂ 范数
        norms[norms == 0] = 1  # 避免除零 (avoid division by zero)
        self.dictionary = dct_matrix / norms  # 归一化后的字典 (normalized dictionary)
    
    def _construct_dct_dictionary(self):
        """
        构造DCT字典矩阵 (Construct DCT Dictionary Matrix)
        
        使用不同频率的DCT基向量构造过完备字典。
        图像和音频信号在此字典下通常具有稀疏表示。
        
        返回:
            DCT字典矩阵，形状为 (n, n)
        """
        # 构造频率域网格 (construct frequency domain grid)
        n = self.n
        dictionary = np.zeros((n, n))  # 初始化字典矩阵
        
        # 生成DCT基向量 (generate DCT basis vectors)
        for f in range(n):
            # 一维DCT基向量 (1D DCT basis vector)
            basis = np.cos(np.pi * f * np.arange(n) / n)
            dictionary[:, f] = basis  # 第f个频率分量
        
        return dictionary  # 返回DCT字典 (return DCT dictionary)
    
    def generate_sparse_signal(self, seed=None):
        """
        生成稀疏信号 (Generate Sparse Signal)
        
        随机选择一个稀疏支撑集，然后在该支撑上赋予随机非零值。
        
        参数:
            seed: 随机种子 (random seed for reproducibility)
        
        返回:
            sparse_signal: 稀疏信号向量 (sparse signal vector)
            support: 支撑集索引 (support set indices)
        """
        if seed is not None:
            np.random.seed(seed)  # 设置随机种子 (set random seed)
        
        # 随机选择k个索引作为支撑集 (randomly select k indices as support)
        support = np.random.choice(self.n, self.k, replace=False)
        support.sort()  # 对支撑集排序 (sort support for consistency)
        
        # 在支撑上赋予随机值 (assign random values on support)
        sparse_signal = np.zeros(self.n)  # 初始化全零信号
        sparse_signal[support] = np.random.randn(self.k)  # 随机非零值
        
        return sparse_signal, support  # 返回稀疏信号和支撑集
    
    def measure(self, signal):
        """
        执行测量过程 (Perform Measurement Process)
        
        将信号投影到测量矩阵上，产生欠采样观测值。
        这模拟了压缩感知中的实际数据采集过程。
        
        参数:
            signal: 输入信号向量 (input signal vector)
        
        返回:
            measurements: 测量向量 (measurement vector)
        """
        measurements = self.measurement_matrix @ signal  # 矩阵乘法得到测量值
        return measurements  # 返回测量结果
    
    def reconstruct_l1(self, measurements, lambda_reg=1e-3):
        """
        ℓ₁范数最小化重建 (ℓ₁ Norm Minimization Reconstruction)
        
        使用基追踪降噪(BPDN)方法求解:
            min ||α||₁ + λ||y - Φ·Ψ·α||₂²
        
        这是一个凸优化问题，可以通过多种方法求解。
        这里使用迭代软阈值算法(ISTA)进行求解。
        
        参数:
            measurements: 测量向量 (measurement vector)
            lambda_reg: 正则化参数 (regularization parameter)
        
        返回:
            reconstructed_signal: 重建信号 (reconstructed signal)
        """
        # 获取矩阵尺寸 (get matrix dimensions)
        m, n = self.measurement_matrix.shape
        d, _ = self.dictionary.shape
        
        # 计算复合矩阵 (compute composite matrix)
        A = self.measurement_matrix @ self.dictionary  # A = Φ·Ψ
        
        # 初始化重建系数 (initialize reconstruction coefficient)
        alpha = np.zeros(d)  # 系数向量 (coefficient vector)
        
        # 计算步长参数 (compute step size)
        # 使用矩阵A的最大奇异值的倒数作为步长
        # Use reciprocal of largest singular value of A as step size
        lipchitz_constant = np.linalg.norm(A, ord=2) ** 2  # Lipschitz常数
        step_size = 1.0 / lipchitz_constant  # 梯度下降步长
        
        # ISTA迭代 (Iterative Shrinkage-Thresholding Algorithm)
        max_iterations = 500  # 最大迭代次数
        tolerance = 1e-6  # 收敛容差 (convergence tolerance)
        
        for iteration in range(max_iterations):
            # 计算梯度 (compute gradient)
            gradient = A.T @ (A @ alpha - measurements)
            
            # 梯度下降 (gradient descent step)
            alpha_temp = alpha - step_size * gradient
            
            # 软阈值算子 (soft-thresholding operator)
            # 解决 min ||α||₁ + (1/2L)||Aα-y||² 的闭式解
            alpha_new = np.sign(alpha_temp) * np.maximum(np.abs(alpha_temp) - lambda_reg * step_size, 0)
            
            # 检查收敛性 (check convergence)
            if np.linalg.norm(alpha_new - alpha) < tolerance:
                break  # 收敛则退出循环
            
            alpha = alpha_new  # 更新系数
        
        # 从稀疏系数重建信号 (reconstruct signal from sparse coefficients)
        reconstructed_signal = self.dictionary @ alpha
        
        return reconstructed_signal  # 返回重建信号


class CompressedSensingProblem:
    """
    压缩感知问题类 (Compressed Sensing Problem Class)
    
    封装压缩感知的完整流程，包括问题建模、求解和评估。
    支持多种重建算法的对比和参数调优。
    
    属性:
        signal_model: 信号模型实例 (signal model instance)
        noise_level: 噪声水平 (noise level)
        reconstruction_error: 重建误差 (reconstruction error)
    """
    
    def __init__(self, n, k, m, noise_level=0.01):
        """
        初始化压缩感知问题 (Initialize Compressed Sensing Problem)
        
        参数:
            n: 信号维度 (signal dimension)
            k: 稀疏度 (sparsity level)
            m: 测量数量 (number of measurements)
            noise_level: 加性高斯噪声标准差 (additive Gaussian noise std)
        """
        self.signal_model = SignalModel(n, k, m)  # 创建信号模型
        self.noise_level = noise_level  # 噪声水平
        self.reconstruction_error = None  # 重建误差
        
    def solve(self, signal, method='l1'):
        """
        求解压缩感知重建问题 (Solve Compressed Sensing Reconstruction Problem)
        
        参数:
            signal: 原始信号向量 (original signal vector)
            method: 求解方法 ('l1': ℓ₁最小化)
        
        返回:
            result: 包含重建信号和误差的字典 (dict with reconstructed signal and error)
        """
        # 执行测量 (perform measurement)
        measurements = self.signal_model.measure(signal)
        
        # 添加噪声模拟实际场景 (add noise to simulate real scenario)
        noise = np.random.randn(len(measurements)) * self.noise_level
        noisy_measurements = measurements + noise
        
        # 选择重建算法 (select reconstruction algorithm)
        if method == 'l1':
            reconstructed = self.signal_model.reconstruct_l1(noisy_measurements)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # 计算重建误差 (compute reconstruction error)
        error = np.linalg.norm(signal - reconstructed) / np.linalg.norm(signal)
        self.reconstruction_error = error
        
        result = {
            'original': signal,
            'reconstructed': reconstructed,
            'error': error,
            'measurements': measurements
        }
        
        return result  # 返回结果字典
    
    def evaluate_quality(self, original, reconstructed):
        """
        评估重建质量 (Evaluate Reconstruction Quality)
        
        计算多种质量评估指标，包括:
        - MSE: 均方误差
        - PSNR: 峰值信噪比
        - NMSE: 归一化均方误差
        
        参数:
            original: 原始信号 (original signal)
            reconstructed: 重建信号 (reconstructed signal)
        
        返回:
            metrics: 质量指标字典 (quality metrics dictionary)
        """
        # 计算均方误差 (compute Mean Squared Error)
        mse = np.mean((original - reconstructed) ** 2)
        
        # 计算峰值信噪比 (compute Peak Signal-to-Noise Ratio)
        if mse > 0:
            psnr = 10 * np.log10(np.max(original) ** 2 / mse)
        else:
            psnr = float('inf')
        
        # 计算归一化均方误差 (compute Normalized MSE)
        nmse = np.linalg.norm(original - reconstructed) ** 2 / np.linalg.norm(original) ** 2
        
        metrics = {
            'mse': mse,
            'psnr': psnr,
            'nmse': nmse
        }
        
        return metrics  # 返回评估指标


def sparsity_pattern(n, k, seed=42):
    """
    生成稀疏模式的辅助函数 (Helper Function for Sparsity Pattern Generation)
    
    参数:
        n: 信号维度 (signal dimension)
        k: 稀疏度 (sparsity level)
        seed: 随机种子 (random seed)
    
    返回:
        mask: 布尔掩码向量 (boolean mask vector)
    """
    np.random.seed(seed)  # 设置随机种子 (set random seed)
    mask = np.zeros(n, dtype=bool)  # 初始化布尔掩码
    indices = np.random.choice(n, k, replace=False)  # 随机选择k个位置
    mask[indices] = True  # 标记为非零位置
    return mask  # 返回稀疏掩码


if __name__ == '__main__':
    """
    测试模块功能 (Test Module Functionality)
    
    运行压缩感知的完整流程，包括:
    1. 信号生成
    2. 测量采集
    3. ℓ₁重建
    4. 质量评估
    
    时间复杂度: O(n·m + m·n_iter) 其中 n_iter 是ISTA迭代次数
    空间复杂度: O(n·m) 用于存储测量矩阵和字典
    """
    print("=" * 60)
    print("压缩感知基础模块测试")
    print("=" * 60)
    
    # 测试参数 (test parameters)
    n = 256  # 信号维度 (signal dimension)
    k = 12   # 稀疏度 (sparsity level)
    m = 64   # 测量数量 (number of measurements)
    noise_level = 0.01  # 噪声水平 (noise level)
    
    print(f"\n信号维度 n = {n}")
    print(f"稀疏度 k = {k}")
    print(f"测量数量 m = {m}")
    print(f"压缩比 = {m/n:.2%}")
    
    # 创建问题实例 (create problem instance)
    problem = CompressedSensingProblem(n, k, m, noise_level)
    
    # 生成测试信号 (generate test signal)
    print("\n生成稀疏测试信号...")
    signal, support = problem.signal_model.generate_sparse_signal(seed=42)
    print(f"支撑集大小: {len(support)}")
    print(f"信号非零元素数: {np.count_nonzero(signal)}")
    
    # 执行重建 (perform reconstruction)
    print("\n执行ℓ₁重建...")
    result = problem.solve(signal, method='l1')
    
    # 评估质量 (evaluate quality)
    print("\n重建质量评估:")
    print(f"重建误差: {result['error']:.6f}")
    
    metrics = problem.evaluate_quality(result['original'], result['reconstructed'])
    print(f"MSE: {metrics['mse']:.6e}")
    print(f"PSNR: {metrics['psnr']:.2f} dB")
    print(f"NMSE: {metrics['nmse']:.6e}")
    
    # 测试不同稀疏度 (test different sparsity levels)
    print("\n" + "=" * 60)
    print("不同稀疏度下的重建性能")
    print("=" * 60)
    
    sparsity_levels = [4, 8, 12, 16, 20]
    errors = []
    
    for k_test in sparsity_levels:
        test_problem = CompressedSensingProblem(n, k_test, m, noise_level)
        test_signal, _ = test_problem.signal_model.generate_sparse_signal(seed=100)
        test_result = test_problem.solve(test_signal, method='l1')
        errors.append(test_result['error'])
        print(f"k = {k_test:2d} | 重建误差 = {test_result['error']:.6f}")
    
    # 分析结果 (analyze results)
    print("\n结论:")
    print("- 稀疏度越高，重建难度越大")
    print("- 测量数量固定时，存在可重建稀疏度的上限")
    print("- ℓ₁最小化在稀疏度满足一定条件时可精确重建")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

"""
算法复杂度分析 (Algorithm Complexity Analysis):

1. 矩阵构造: O(n²) 用于DCT字典构造
2. 测量过程: O(m·n) 单次矩阵乘法
3. ISTA迭代: O(m·n·T) 其中T为迭代次数
4. 总体重建: O(m·n·T + n²)

空间复杂度:
- 测量矩阵存储: O(m·n)
- 字典存储: O(n²)
- 迭代变量: O(n)

关键参数影响:
- 稀疏度k: 影响收敛速度和重建质量
- 测量数m: 影响压缩比和信息损失
- 正则化λ: 影响稀疏性和保真度的权衡
"""
