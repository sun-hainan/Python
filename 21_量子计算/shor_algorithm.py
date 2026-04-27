# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / shor_algorithm

本文件实现 shor_algorithm 相关的算法功能。
"""

import numpy as np
import math
from fractions import Fraction


# =============================================================================
# 经典辅助函数 (Classical Helper Functions)
# =============================================================================

def gcd(a, b):
    """
    计算两个整数的最大公约数（欧几里得算法）
    
    Args:
        a: 第一个整数
        b: 第二个整数
        
    Returns:
        gcd(a, b)
    """
    while b != 0:
        a, b = b, a % b
    return abs(a)


def extended_gcd(a, b):
    """
    扩展欧几里得算法 - 求gcd(a,b)以及系数x,y使得ax+by=gcd(a,b)
    
    Args:
        a, b: 两个整数
        
    Returns:
        (g, x, y) 其中 g=gcd(a,b), x,y为系数
    """
    if b == 0:
        return (a, 1, 0)
    else:
        g, x1, y1 = extended_gcd(b, a % b)
        x = y1
        y = x1 - (a // b) * y1
        return (g, x, y)


def is_prime(n):
    """判断整数n是否为素数"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def modular_exponent(base, exponent, modulus):
    """
    计算模指数: base^exponent mod modulus
    
    使用快速幂算法
    
    Args:
        base: 底数
        exponent: 指数
        modulus: 模数
        
    Returns:
        (base^exponent) mod modulus
    """
    if modulus == 1:
        return 0
    result = 1
    base = base % modulus
    while exponent > 0:
        if exponent % 2 == 1:
            result = (result * base) % modulus
        exponent //= 2
        base = (base * base) % modulus
    return result


# =============================================================================
# 连分数展开 (Continued Fraction Expansion)
# =============================================================================

def continued_fraction_expansion(y, denominator_limit):
    """
    求y的连分数展开
    
    连分数展开用于从近似分数恢复有理数
    
    Args:
        y: 实数（通常是小数近似）
        denominator_limit: 分母上限
        
    Returns:
        Fraction对象，表示最接近y的有理数
    """
    # 初始化
    h_prev, h_curr = 0, 1  # 分子序列
    k_prev, k_curr = 1, 0  # 分母序列
    a_int = int(math.floor(y))
    
    while True:
        # 连分数的系数
        a = int(math.floor(y))
        
        # 更新分子分母
        h_next = a * h_curr + h_prev
        k_next = a * k_curr + k_prev
        
        # 检查分母是否超过限制
        if k_next > denominator_limit or k_next == 0:
            break
        
        # 更新变量
        h_prev, h_curr = h_curr, h_next
        k_prev, k_curr = k_curr, k_next
        
        # 更新y
        if a == int(y):
            break
        y = 1 / (y - a)
        
        if y > 1e10:  # 避免无穷大
            break
    
    # 返回最接近的结果
    return Fraction(h_curr, k_curr)


def find_order_from_measurement(measurement, num_qubits, a, N):
    """
    从量子测量结果找到阶r
    
    使用连分数展开从测量值推断真正的阶
    
    Args:
        measurement: 量子计算机测量的整数值
        num_qubits: 量子比特数
        a: 底数
        N: 待分解的整数
        
    Returns:
        可能的阶r
    """
    if measurement == 0:
        return None
    
    # 测量值对应的是 j/r，其中j是某个整数
    # 使用连分数展开得到 j/r 的近似
    phase = measurement / (2 ** num_qubits)
    
    # 连分数展开
    frac = continued_fraction_expansion(phase, 2 ** num_qubits)
    
    if frac.denominator == 0:
        return None
    
    r = frac.denominator
    
    # 检查r是否为有效的阶
    if r == 0 or r > N:
        return None
    
    # 验证 a^r ≡ 1 (mod N)
    if modular_exponent(a, r, N) == 1:
        return r
    
    # 如果不对，尝试倍数
    for k in range(2, 4):
        if k * r != 0 and k * r <= N:
            if modular_exponent(a, k * r, N) == 1:
                return k * r
    
    return None


# =============================================================================
# 量子模指数运算 (Quantum Modular Exponentiation)
# =============================================================================

def create_modular_exponent_matrix(a, N, num_qubits):
    """
    创建模指数运算的矩阵表示
    
    这个函数模拟量子模指数运算 |x⟩ → |a^x mod N⟩
    
    注意：这是简化的经典模拟，真正的量子计算机使用量子电路
    
    Args:
        a: 底数
        N: 模数
        num_qubits: 量子比特数
        
    Returns:
        模指数矩阵（2^n × 2^n）
    """
    dimension = 2 ** num_qubits
    matrix = np.zeros((dimension, dimension), dtype=complex)
    
    for x in range(dimension):
        y = modular_exponent(a, x, N)
        matrix[y, x] = 1.0
    
    return matrix


def quantum_fourier_transform(num_qubits):
    """
    生成量子傅里叶变换(QFT)矩阵
    
    QFT: |j⟩ → (1/√N) Σ_k exp(2πi jk/N) |k⟩
    
    Args:
        num_qubits: 量子比特数
        
    Returns:
        QFT矩阵（2^n × 2^n）
    """
    dimension = 2 ** num_qubits
    omega = np.exp(2j * np.pi / dimension)  # e^(2πi/N)
    qft = np.zeros((dimension, dimension), dtype=complex)
    
    for j in range(dimension):
        for k in range(dimension):
            qft[k, j] = omega ** (j * k) / np.sqrt(dimension)
    
    return qft


def simulate_shor_quantum_part(a, N, num_qubits=None):
    """
    模拟Shor算法的量子部分
    
    步骤：
    1. 初始叠加态
    2. 模指数运算
    3. 量子傅里叶变换
    4. 测量
    
    Args:
        a: 底数
        N: 待分解整数
        num_qubits: 量子比特数（默认为log₂(N)的2倍）
        
    Returns:
        measurement: 测量结果
        phase: 相位值
    """
    if num_qubits is None:
        num_qubits = math.ceil(2 * math.log2(N))
    
    dimension = 2 ** num_qubits
    
    # 步骤1：初始叠加态 |0⟩ + |1⟩ + ... + |N-1⟩
    initial_state = np.zeros(dimension, dtype=complex)
    for i in range(min(N, dimension)):
        initial_state[i] = 1.0
    initial_state /= np.sqrt(min(N, dimension))
    
    # 步骤2：模指数运算
    mod_exp_matrix = create_modular_exponent_matrix(a, N, num_qubits)
    state_after_mod = mod_exp_matrix @ initial_state
    
    # 步骤3：量子傅里叶变换
    qft_matrix = quantum_fourier_transform(num_qubits)
    state_after_qft = qft_matrix @ state_after_mod
    
    # 步骤4：测量
    probabilities = np.abs(state_after_qft) ** 2
    measurement = np.random.choice(dimension, p=probabilities)
    phase = measurement / dimension
    
    return measurement, phase


# =============================================================================
# Shor算法核心 (Shor Algorithm Core)
# =============================================================================

class ShorFactorization:
    """
    Shor量子因数分解算法实现类
    
    Attributes:
        N: 待分解的整数
        a: 随机选择的底数
        factors: 找到的因子列表
    """
    
    def __init__(self, N):
        """
        初始化Shor算法
        
        Args:
            N: 待分解的正整数（应为奇数，且不是素数的幂）
        """
        if N % 2 == 0:
            raise ValueError("N是偶数，请先除以2")
        self.N = N
        self.factors = []
        self.a = None
        self.order = None
    
    def find_factors(self):
        """
        尝试分解N直到找到因子
        
        Returns:
            (factor1, factor2) 或 None
        """
        max_attempts = 10
        
        for attempt in range(max_attempts):
            print(f"\n尝试 {attempt + 1}:")
            
            # 步骤1：随机选择a (2 <= a < N)
            self.a = np.random.randint(2, self.N - 1)
            print(f"  选择 a = {self.a}")
            
            # 检查是否互素
            g = gcd(self.a, self.N)
            if g > 1:
                print(f"  gcd({self.a}, {self.N}) = {g}，找到因子!")
                return (g, self.N // g)
            
            # 步骤2：求a的阶r（量子部分）
            print(f"  求 a={self.a} 的阶...")
            self.order = self._find_order_quantum()
            
            if self.order is None:
                print(f"  无法找到有效的阶，继续尝试...")
                continue
            
            print(f"  找到阶 r = {self.order}")
            
            if self.order % 2 != 0:
                print(f"  r是奇数，选择不同的a")
                continue
            
            # 步骤3：计算因子
            factor1, factor2 = self._compute_factors()
            
            if factor1 is not None:
                return (factor1, factor2)
        
        return None
    
    def _find_order_quantum(self):
        """
        使用量子模拟找到a的阶
        
        Returns:
            阶r或None
        """
        num_qubits = math.ceil(2 * math.log2(self.N))
        
        for _ in range(20):  # 多次尝试
            measurement, phase = simulate_shor_quantum_part(self.a, self.N, num_qubits)
            
            if measurement == 0:
                continue
            
            r = find_order_from_measurement(measurement, num_qubits, self.a, self.N)
            
            if r is not None and modular_exponent(self.a, r, self.N) == 1:
                return r
        
        return None
    
    def _compute_factors(self):
        """
        从阶r计算因子
        
        如果 a^(r/2) ± 1 与 N 不互素，则找到因子
        
        Returns:
            (factor1, factor2) 或 (None, None)
        """
        r_over_2 = self.order // 2
        a_power = modular_exponent(self.a, r_over_2, self.N)
        
        print(f"  a^(r/2) = {self.a}^{self.order//2} mod {self.N} = {a_power}")
        
        # 计算 gcd(a^(r/2) - 1, N)
        factor1 = gcd(a_power - 1, self.N)
        if factor1 > 1 and factor1 < self.N:
            factor2 = self.N // factor1
            print(f"  因子: gcd({a_power}-1, {self.N}) = {factor1}")
            return (factor1, factor2)
        
        # 计算 gcd(a^(r/2) + 1, N)
        factor1 = gcd(a_power + 1, self.N)
        if factor1 > 1 and factor1 < self.N:
            factor2 = self.N // factor1
            print(f"  因子: gcd({a_power}+1, {self.N}) = {factor1}")
            return (factor1, factor2)
        
        return (None, None)


def shor_factor(N):
    """
    Shor算法的便捷函数接口
    
    Args:
        N: 待分解的整数
        
    Returns:
        (factor1, factor2) 其中 N = factor1 * factor2
    """
    if N % 2 == 0:
        return (2, N // 2)
    
    if is_prime(N):
        print(f"{N} 是素数，无法分解")
        return None
    
    factorizer = ShorFactorization(N)
    result = factorizer.find_factors()
    
    if result:
        f1, f2 = result
        print(f"\n分解成功: {N} = {f1} × {f2}")
        return result
    else:
        print(f"\n无法分解 {N}")
        return None


# =============================================================================
# 测试代码 (Test Code)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Shor量子因数分解算法测试")
    print("=" * 70)
    
    # 测试1：简单的偶数分解
    print("\n【测试1】偶数分解 (不需要量子算法)")
    print("分解 N = 21")
    
    # 手动测试gcd
    for a in range(2, 20):
        g = gcd(a, 21)
        if g > 1:
            print(f"  a = {a}, gcd({a}, 21) = {g}, 因子 = ({g}, {21//g})")
            break
    
    # 测试2：模拟量子阶求解
    print("\n" + "-" * 70)
    print("\n【测试2】模拟量子阶求解")
    
    N_test = 15
    a_test = 7
    
    print(f"求 a = {a_test} 模 N = {N_test} 的阶")
    
    # 经典方法验证
    for r in range(1, 30):
        if modular_exponent(a_test, r, N_test) == 1:
            print(f"  阶 r = {r} (经典计算)")
            break
    
    # 量子模拟
    measurement, phase = simulate_shor_quantum_part(a_test, N_test)
    print(f"  量子测量结果: {measurement}")
    print(f"  相位: {phase:.6f}")
    
    # 连分数恢复
    frac = continued_fraction_expansion(phase, 100)
    print(f"  连分数近似: {frac}")
    
    # 测试3：完整的Shor算法分解
    print("\n" + "-" * 70)
    print("\n【测试3】完整Shor算法分解 N = 15")
    
    print("尝试分解 15 = 3 × 5")
    factors = shor_factor(15)
    if factors:
        print(f"结果: {factors[0]} × {factors[1]}")
    
    # 测试4：分解更大的数
    print("\n" + "-" * 70)
    print("\n【测试4】分解 N = 21")
    
    factors_21 = shor_factor(21)
    if factors_21:
        print(f"结果: {factors_21[0]} × {factors_21[1]}")
    
    # 测试5：分解 N = 33
    print("\n" + "-" * 70)
    print("\n【测试5】分解 N = 33 (3 × 11)")
    
    factors_33 = shor_factor(33)
    if factors_33:
        print(f"结果: {factors_33[0]} × {factors_33[1]}")
    
    # 测试6：模指数运算验证
    print("\n" + "-" * 70)
    print("\n【测试6】模指数运算验证")
    
    test_cases = [
        (3, 5, 7),   # 3^5 mod 7
        (2, 10, 100),  # 2^10 mod 100
        (7, 123, 1000),  # 7^123 mod 1000
    ]
    
    for base, exp, mod in test_cases:
        result = modular_exponent(base, exp, mod)
        print(f"  {base}^{exp} mod {mod} = {result}")
    
    # 测试7：连分数展开
    print("\n" + "-" * 70)
    print("\n【测试7】连分数展开")
    
    test_fracs = [0.333333, 0.1415926535, 0.7071067812]
    for y in test_fracs:
        frac = continued_fraction_expansion(y, 1000)
        print(f"  {y:.6f} → {frac} ≈ {float(frac):.6f}")
    
    print("\n" + "=" * 70)
    print("Shor算法测试完成！")
    print("=" * 70)
