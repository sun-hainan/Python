# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_random

本文件实现 quantum_random 相关的算法功能。
"""

import numpy as np  # 导入NumPy用于数值计算


# =============================================================================
# 辅助函数 - Helper Functions
# =============================================================================

def signal_to_bits(photons_detected, threshold=0.5):
    """
    将光子检测信号转换为比特流。

    参数：
        photons_detected: array, 每个时间窗口检测到的光子数（归一化到[0,1]）
        threshold: float, 判决门限（默认0.5）

    返回：
        list: 二进制比特列表（0或1）
    """
    # 小于阈值判定为0，大于等于判定为1
    bits = [1 if p >= threshold else 0 for p in photons_detected]
    return bits


# =============================================================================
# 单光子随机比特生成 - Single Photon Random Bit Generation
# =============================================================================

class QuantumRandomGenerator:
    """
    基于单光子探测的量子随机数生成器。

    原理：
        当单光子入射到50:50分束器（BS）时：
        - 光子有50%概率透射，50%概率反射
        - 检测到哪个探测器响应完全随机
        - 无法预测，与任何隐变量无关

    使用方式：
        qrng = QuantumRandomGenerator()
        bits = qrng.generate_bits(n=128)  # 生成128比特
    """

    def __init__(self, seed=None):
        """
        初始化QRNG。

        参数：
            seed: 伪随机种子（仅用于模拟，实际硬件无需种子）
                  设为None时使用系统 entropy
        """
        # 注意：在真实硬件中，这个seed不影响量子过程
        # 这里仅用于模拟检测器的响应噪声
        if seed is not None:
            np.random.seed(seed)

        # 模拟检测器效率（理想情况为1）
        self.detector_efficiency = 0.98

        # 模拟暗计数率（每秒错误计数）
        self.dark_count_rate = 1e-6

        # 已生成的总比特数（用于监测）
        self.total_bits_generated = 0

    def photon_detection_probability(self, path='reflect'):
        """
        模拟单光子到达探测器并被检测到的概率。

        物理模型：
        - 光子到达：服从泊松分布（平均光子数λ）
        - 分束器决策：50%透射，50%反射
        - 探测器响应：效率×到达概率 + 暗计数

        参数：
            path: 'transmit' 或 'reflect'，表示光子的路径

        返回：
            bool: True表示该路径探测器响应
        """
        # 光子到达（泊松过程，λ=1表示平均1个光子）
        mean_photons = 1.0
        n_photons = np.random.poisson(mean_photons)

        if n_photons == 0:
            # 无光子到达
            return False

        # 分束器随机路由
        if path == 'reflect':
            # 反射光被探测器接收
            detected = np.random.random() < self.detector_efficiency
        else:
            # 透射光被另一探测器接收
            detected = np.random.random() < self.detector_efficiency

        # 暗计数（假触发）
        dark_count = np.random.random() < self.dark_count_rate

        return detected or dark_count

    def generate_single_bit(self):
        """
        生成单个量子随机比特。

        原理：
            单光子入射50:50分束器，两个输出端口各接一个探测器。
            检测到哪个端口响应即为随机比特。

        返回：
            int: 0或1
        """
        # 两个探测器同时响应时（极其罕见），重新生成
        while True:
            # 检测反射路径
            reflect_detected = self.photon_detection_probability('reflect')
            # 检测透射路径
            transmit_detected = self.photon_detection_probability('transmit')

            # 判决规则：哪个探测器先响应就是哪个
            # 模拟中用随机性代替时序
            if reflect_detected and not transmit_detected:
                return 0
            elif transmit_detected and not reflect_detected:
                return 1
            # 其他情况（无响应或同时响应）重新生成

    def generate_bits(self, n=128):
        """
        生成指定长度的量子随机比特序列。

        参数：
            n: 要生成的比特数（默认128）

        返回：
            list: 长度为n的比特列表
        """
        bits = []
        for _ in range(n):
            bits.append(self.generate_single_bit())
            self.total_bits_generated += 1

        return bits

    def generate_byte(self):
        """
        生成一个随机字节（8比特）。

        返回：
            int: 0-255之间的随机整数
        """
        bits = self.generate_bits(8)
        byte_val = 0
        for i, bit in enumerate(bits):
            byte_val |= (bit << i)
        return byte_val

    def generate_bytes(self, n_bytes=16):
        """
        生成指定数量的随机字节。

        参数：
            n_bytes: 字节数量

        返回：
            bytes: 随机字节串
        """
        result = bytearray()
        for _ in range(n_bytes):
            result.append(self.generate_byte())
        return bytes(result)

    def generate_integer(self, low=0, high=100):
        """
        生成指定范围内的随机整数。

        参数：
            low: 下界（包含）
            high: 上界（不包含）

        返回：
            int: 范围内的随机整数
        """
        # 计算需要多少比特表示该范围
        range_size = high - low
        n_bits = int(np.ceil(np.log2(range_size)))

        # 生成额外比特以减少偏差
        extra_bits = n_bits + 8
        bits = self.generate_bits(extra_bits)

        # 转换为整数
        val = 0
        for bit in bits:
            val = (val << 1) | bit

        # 映射到目标范围
        return low + (val % range_size)

    def entropy_rate(self):
        """
        估算当前生成器的信息熵率。

        返回：
            float: 每比特的信息熵（理想值为1）
        """
        # 模拟检测：取最近生成的100比特计算0/1比例
        sample_size = min(100, self.total_bits_generated)
        if sample_size < 10:
            return 1.0  # 数据不足

        # 生成样本
        sample_bits = self.generate_bits(sample_size)
        p1 = sum(sample_bits) / sample_size
        p0 = 1 - p1

        # Shannon熵 H = -sum(p log2 p)
        if p0 == 0 or p1 == 0:
            return 0.0
        entropy = -(p0 * np.log2(p0) + p1 * np.log2(p1))

        return entropy


# =============================================================================
# 随机数质量测试 - Randomness Quality Tests
# =============================================================================

class RandomnessTest:
    """
    随机数质量测试套件（简化版NIST SP 800-20）。

    包含以下测试：
        - 单比特频率测试（Monobit）
        - 块内频率测试（Block Frequency）
        - 游程测试（Runs Test）
        - 二阶熵测试
    """

    @staticmethod
    def monobit_test(bits):
        """
        单比特频率测试（Monobit Test）。

        检验比特序列中0和1的出现次数是否接近相等。
        通过条件：|n_ones - n_zeros| / N < threshold

        参数：
            bits: 比特列表

        返回：
            dict: 包含统计量和通过状态
        """
        n = len(bits)
        n_ones = sum(bits)
        n_zeros = n - n_ones

        # 计算偏差
        deviation = abs(n_ones - n_zeros) / n

        # 通过阈值（95%置信度下）
        threshold = 1.96 / np.sqrt(n)

        return {
            'n_ones': n_ones,
            'n_zeros': n_zeros,
            'deviation': deviation,
            'threshold': threshold,
            'passed': deviation < threshold
        }

    @staticmethod
    def block_frequency_test(bits, block_size=1000):
        """
        块内频率测试（Block Frequency Test）。

        将序列分成多个块，检验每个块内1的比例是否接近0.5。
        适用于检测块相关的偏差。

        参数：
            bits: 比特列表
            block_size: 每个块的大小（默认1000）

        返回：
            dict: 包含各块比例和整体评估
        """
        n = len(bits)
        n_blocks = n // block_size

        if n_blocks < 1:
            return {'passed': False, 'reason': '序列长度不足'}

        proportions = []
        for i in range(n_blocks):
            block = bits[i * block_size:(i + 1) * block_size]
            proportion = sum(block) / block_size
            proportions.append(proportion)

        # 卡方统计量
        chi_sq = 0
        for p in proportions:
            chi_sq += (p - 0.5) ** 2

        chi_sq *= 4 * block_size

        # 自由度 = n_blocks，卡方检验阈值（0.01显著水平）
        from scipy.stats import chi2  # 延迟导入避免scipy缺失时崩溃
        critical_value = chi2.ppf(0.99, n_blocks - 1)

        return {
            'n_blocks': n_blocks,
            'proportions': proportions,
            'chi_square': chi_sq,
            'critical_value': critical_value,
            'passed': chi_sq < critical_value
        }

    @staticmethod
    def runs_test(bits):
        """
        游程测试（Runs Test）。

        游程：连续相同比特的序列。
        检验游程数量是否符合随机序列的预期。

        参数：
            bits: 比特列表

        返回：
            dict: 包含游程数和统计检验结果
        """
        if len(bits) < 20:
            return {'passed': False, 'reason': '序列太短'}

        # 转换为 ±1 序列
        x = [1 if b == 1 else -1 for b in bits]

        # 计算游程数
        runs = 1
        for i in range(1, len(x)):
            if x[i] != x[i - 1]:
                runs += 1

        # 计算检验统计量
        n = len(bits)
        n_ones = sum(bits)

        # 期望游程数
        expected_runs = 2 * n_ones * (n - n_ones) / n + 1

        # 标准差
        if n_ones == 0 or n_ones == n:
            return {'passed': False, 'reason': '序列全0或全1'}

        var = (2 * n_ones * n_zeros * (2 * n_ones - n - 1)) / (n ** 2 * (n - 1))
        n_zeros = n - n_ones

        # Z统计量
        z = (runs - expected_runs) / np.sqrt(var) if var > 0 else 0

        # 检验：|Z| < 1.96 则通过
        return {
            'runs': runs,
            'expected_runs': expected_runs,
            'z_score': z,
            'passed': abs(z) < 1.96
        }

    @staticmethod
    def entropy_test(bits):
        """
        二阶熵测试（Entropy Test）。

        计算比特序列的Shannon熵，理想随机序列的熵应接近1。

        参数：
            bits: 比特列表

        返回：
            dict: 包含估计熵值和判断
        """
        n = len(bits)
        n_ones = sum(bits)
        n_zeros = n - n_ones

        # 概率估计
        p1 = n_ones / n
        p0 = n_zeros / n

        # Shannon熵（每比特）
        if p0 == 0 or p1 == 0:
            entropy = 0.0
        else:
            entropy = -(p0 * np.log2(p0) + p1 * np.log2(p1))

        return {
            'entropy': entropy,
            'max_entropy': 1.0,
            'ratio': entropy,
            'passed': entropy > 0.95  # 阈值设为0.95
        }

    @staticmethod
    def run_all_tests(bits, block_size=1000):
        """
        运行所有随机性测试并生成报告。

        参数：
            bits: 比特列表
            block_size: 块测试的块大小

        返回：
            dict: 包含所有测试结果和总体评估
        """
        results = {
            'monobit': RandomnessTest.monobit_test(bits),
            'entropy': RandomnessTest.entropy_test(bits),
            'runs': RandomnessTest.runs_test(bits)
        }

        if len(bits) >= block_size:
            results['block_frequency'] = RandomnessTest.block_frequency_test(bits, block_size)

        # 总体通过：所有测试都通过
        all_passed = all(r.get('passed', False) for r in results.values())

        results['overall_passed'] = all_passed

        return results


# =============================================================================
# 密码学应用 - Cryptographic Applications
# =============================================================================

class QuantumKeyGenerator:
    """
    基于量子随机数的密码学密钥生成器。

    功能：
        - 生成指定长度的对称加密密钥
        - 生成初始化向量（IV）
        - 生成盐值（salt）
        - 生成nonce

    用途：
        - AES密钥（128/192/256位）
        - 初始化向量
        - 密钥派生函数的盐
    """

    def __init__(self, qrng=None):
        """
        初始化密钥生成器。

        参数：
            qrng: QuantumRandomGenerator实例，None则创建新实例
        """
        self.qrng = qrng if qrng is not None else QuantumRandomGenerator()

    def generate_aes_key(self, key_size=128):
        """
        生成AES密钥。

        参数：
            key_size: 密钥位数（128、192或256）

        返回：
            bytes: 密钥字节串
        """
        # 验证参数
        valid_sizes = [128, 192, 256]
        if key_size not in valid_sizes:
            raise ValueError(f"密钥大小必须是{valid_sizes}之一")

        n_bytes = key_size // 8
        return self.qrng.generate_bytes(n_bytes)

    def generate_iv(self, size=128):
        """
        生成初始化向量（IV）。

        参数：
            size: IV位数（默认128）

        返回：
            bytes: IV字节串
        """
        n_bytes = size // 8
        return self.qrng.generate_bytes(n_bytes)

    def generate_nonce(self, size=96):
        """
        生成nonce（只用一次的数）。

        参数：
            size: nonce位数（默认96，用于AES-GCM）

        返回：
            bytes: nonce字节串
        """
        n_bytes = size // 8
        return self.qrng.generate_bytes(n_bytes)

    def generate_salt(self, size=128):
        """
        生成盐值用于密钥派生（PBKDF2、Argon2等）。

        参数：
            size: 盐值位数（默认128）

        返回：
            bytes: 盐值字节串
        """
        n_bytes = size // 8
        return self.qrng.generate_bytes(n_bytes)

    def generate_password(self, length=16):
        """
        生成随机密码（字母数字混合）。

        参数：
            length: 密码长度

        返回：
            str: 随机密码
        """
        # 字符集：a-z, A-Z, 0-9
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

        # 每个位置随机选择字符
        indices = [self.qrng.generate_integer(0, len(chars)) for _ in range(length)]

        password = ''.join(chars[i] for i in indices)
        return password


# =============================================================================
# 主程序测试 - Main Test
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("量子随机数生成器测试")
    print("=" * 60)

    # 1. 测试基本生成
    print("\n[1] 单比特生成测试")
    print("-" * 40)
    qrng = QuantumRandomGenerator(seed=42)  # 用于重现性
    bits = qrng.generate_bits(20)
    print(f"  生成的20比特: {bits}")
    print(f"  1的数量: {sum(bits)}, 0的数量: {len(bits) - sum(bits)}")

    # 2. 测试随机数质量
    print("\n[2] 随机性测试（10000比特）")
    print("-" * 40)

    qrng = QuantumRandomGenerator()  # 无seed，真随机
    test_bits = qrng.generate_bits(10000)

    results = RandomnessTest.run_all_tests(test_bits)
    for test_name, result in results.items():
        if test_name == 'overall_passed':
            continue
        status = "✅ 通过" if result.get('passed') else "❌ 失败"
        if test_name == 'monobit':
            print(f"  {test_name}: deviation={result['deviation']:.4f}, threshold={result['threshold']:.4f} {status}")
        elif test_name == 'entropy':
            print(f"  {test_name}: entropy={result['entropy']:.4f} {status}")
        elif test_name == 'runs':
            print(f"  {test_name}: runs={result['runs']}, expected={result['expected_runs']:.0f} {status}")
        elif test_name == 'block_frequency':
            print(f"  {test_name}: blocks={result['n_blocks']}, chi_sq={result['chi_square']:.2f} {status}")

    print(f"\n  总体评估: {'✅ 所有测试通过' if results['overall_passed'] else '❌ 部分测试失败'}")

    # 3. 测试密码学应用
    print("\n[3] 密码学密钥生成")
    print("-" * 40)

    key_gen = QuantumKeyGenerator(qrng)

    aes_128 = key_gen.generate_aes_key(128)
    aes_256 = key_gen.generate_aes_key(256)
    iv = key_gen.generate_iv()
    nonce = key_gen.generate_nonce()
    password = key_gen.generate_password(16)

    print(f"  AES-128密钥 (hex): {aes_128.hex()[:32]}...")
    print(f"  AES-256密钥 (hex): {aes_256.hex()[:32]}...")
    print(f"  IV (hex): {iv.hex()}")
    print(f"  Nonce (hex): {nonce.hex()}")
    print(f"  随机密码: {password}")

    # 4. 对比量子随机 vs 伪随机
    print("\n[4] 量子随机 vs 伪随机对比")
    print("-" * 40)

    # 伪随机（线性同余）
    class PseudoRandom:
        def __init__(self, seed):
            self.state = seed
            self.a = 1664525
            self.c = 1013904223
            self.m = 2 ** 32

        def generate(self):
            self.state = (self.a * self.state + self.c) % self.m
            return self.state

    prng = PseudoRandom(seed=42)
    prng_bits = [1 if prng.generate() % 2 == 1 else 0 for _ in range(10000)]

    q_entropy = RandomnessTest.entropy_test(test_bits)['entropy']
    p_entropy = RandomnessTest.entropy_test(prng_bits)['entropy']

    print(f"  量子随机熵: {q_entropy:.6f} (理想值: 1.000000)")
    print(f"  伪随机熵:   {p_entropy:.6f}")
    print(f"  说明: 伪随机序列存在周期性，熵略低")

    # 5. 熵率监测
    print("\n[5] 熵率监测")
    print("-" * 40)

    qrng = QuantumRandomGenerator()
    for n in [100, 1000, 10000]:
        qrng.generate_bits(n)
        rate = qrng.entropy_rate()
        print(f"  {n}比特后熵率: {rate:.6f}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
