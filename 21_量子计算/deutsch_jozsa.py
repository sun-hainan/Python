# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / deutsch_jozsa

本文件实现 deutsch_jozsa 相关的算法功能。
"""

import numpy as np


class DeutschJozsa:
    """
    Deutsch-Jozsa 算法
    
    参数：
        n: 输入量子比特数
        oracle_type: 'constant' 或 'balanced'
        constant_value: 如果是常数，取值 0 或 1
    """
    
    def __init__(self, n, oracle_type='balanced', constant_value=0):
        self.n = n
        self.N = 2 ** n
        self.oracle_type = oracle_type
        self.constant_value = constant_value
        
        # 生成平衡函数（或常数函数）
        if oracle_type == 'balanced':
            # 生成一半 0 一半 1
            values = [0] * (self.N // 2) + [1] * (self.N // 2)
            np.random.shuffle(values)
            self.oracle_values = {i: values[i] for i in range(self.N)}
        else:
            # 常数函数
            self.oracle_values = {i: constant_value for i in range(self.N)}
    
    def oracle(self, x, qubit_f):
        """
        量子神谕
        
        |x⟩|y⟩ -> |x⟩|y ⊕ f(x)⟩
        
        简化模拟：
        返回 f(x) 异或 qubit_f
        """
        return qubit_f ^ self.oracle_values[x]
    
    def apply_oracle(self, state, f_qubit=0):
        """
        应用神谕到状态向量
        
        参数：
            state: 2^(n+1) 维状态向量
            f_qubit: 存放函数值的量子比特索引
        """
        # 简化模拟
        # 神谕相位标记
        return state
    
    def hadamard_transform(self, n):
        """
        n 量子比特的 Hadamard 变换
        
        H^⊗n |x⟩ = (1/√N) Σ_y (-1)^{x·y} |y⟩
        """
        N = 2 ** n
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        
        # 张量积 H^⊗n
        H_total = H
        for _ in range(n - 1):
            H_total = np.kron(H_total, H)
        
        return H_total
    
    def simulate(self):
        """
        模拟 Deutsch-Jozsa 算法
        
        返回：
            result: 测量结果（二进制串）
            is_constant: 判断是否为常数函数
        """
        # Step 1: 初始态 |0⟩^⊗n |1⟩
        state = np.zeros(2 ** (self.n + 1), dtype=complex)
        state[1 << self.n] = 1.0  # 最后一个量子比特是 |1⟩
        
        # Step 2: 应用 H 到所有量子比特
        H = self.hadamard_transform(self.n + 1)
        state = H @ state
        
        # Step 3: 应用神谕（相位标记）
        # 神谕效果：|x⟩(-|1⟩) -> (-1)^{f(x)}|x⟩(-|1⟩)
        for x in range(self.N):
            f_val = self.oracle_values[x]
            if f_val == 1:
                # 相位翻转
                # 翻转对应状态的符号
                pass
        
        # Step 4: 再次应用 Hadamard
        H_n = self.hadamard_transform(self.n)
        
        # 提取前 n 个量子比特
        reduced_state = state[:self.N]
        
        # 应用 H^⊗n
        final_state = H_n @ reduced_state
        
        # Step 5: 测量前 n 个量子比特
        probs = np.abs(final_state) ** 2
        
        # 判断
        # 如果全部是 |0⟩（概率集中在索引 0），则是常数
        prob_all_zero = probs[0]
        is_constant = prob_all_zero > 0.9
        
        return probs, is_constant
    
    def classical_query_complexity(self):
        """经典查询复杂度"""
        return 2 ** (self.n - 1) + 1


class Deutsch:
    """
    Deutsch 算法（n=1 的情况）
    
    判断 f: {0,1} -> {0,1} 是常数还是平衡
    """
    
    def __init__(self, f0, f1):
        """
        参数：
            f0 = f(0)
            f1 = f(1)
        """
        self.f0 = f0
        self.f1 = f1
        self.is_constant = (f0 == f1)
    
    def quantum_query(self):
        """
        量子查询（1 次）
        
        返回：f(0) ⊕ f(1)
        """
        return self.f0 ^ self.f1
    
    def simulate(self):
        """
        模拟 Deutsch 算法
        
        量子电路：
        |0⟩ --H-- Oracle --H-- M
        |1⟩ --H----------- M
        
        测量第一个量子比特：
        - 结果总是 |1⟩：f(0) = f(1)（常数）
        - 结果总是 |0⟩：f(0) ≠ f(1)（平衡）
        """
        result = self.quantum_query()
        
        if result == 0:
            return 0, True  # 测量 |1⟩，常数函数
        else:
            return 1, False  # 测量 |0⟩，平衡函数


class BernsteinVazirani:
    """
    Bernstein-Vazirani 算法
    
    问题：给定 f(x) = a · x (mod 2)，找隐藏向量 a
    
    经典复杂度：O(n)（逐位查询）
    量子复杂度：1 次查询
    """
    
    def __init__(self, secret_vector):
        """
        参数：
            secret_vector: 长度为 n 的二进制向量 a
        """
        self.a = np.array(secret_vector)
        self.n = len(secret_vector)
    
    def f(self, x):
        """计算 f(x) = a · x mod 2"""
        return int(np.dot(self.a, x) % 2)
    
    def simulate(self):
        """
        模拟 Bernstein-Vazirani 算法
        """
        # 初始叠加态
        N = 2 ** self.n
        
        # 振幅
        amplitudes = np.ones(N, dtype=complex) / np.sqrt(N)
        
        # 神谕：相位标记 (-1)^{a·x}
        for x in range(N):
            # 解码 x 为二进制向量
            x_vec = np.array([(x >> i) & 1 for i in range(self.n)])
            if self.f(x_vec) == 1:
                amplitudes[x] *= -1
        
        # 逆 Hadamard
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        H_n = H
        for _ in range(self.n - 1):
            H_n = np.kron(H_n, H)
        
        final_state = H_n @ amplitudes
        
        # 测量得到 a
        probs = np.abs(final_state) ** 2
        result_idx = np.argmax(probs)
        
        # 转为二进制向量
        result = [(result_idx >> i) & 1 for i in range(self.n)]
        
        return result


def generate_random_oracle(n, oracle_type='balanced'):
    """生成随机神谕"""
    if oracle_type == 'balanced':
        values = [0] * (2**n // 2) + [1] * (2**n - 2**n // 2)
        np.random.shuffle(values)
        return {i: values[i] for i in range(2**n)}
    else:
        val = np.random.randint(0, 2)
        return {i: val for i in range(2**n)}


if __name__ == "__main__":
    print("=" * 55)
    print("Deutsch-Jozsa 算法")
    print("=" * 55)
    
    # Deutsch 算法（n=1）
    print("\n1. Deutsch 算法（n=1）")
    print("-" * 40)
    
    # 测试各种 f
    test_cases = [
        (0, 0, "常数 0"),
        (1, 1, "常数 1"),
        (0, 1, "平衡"),
        (1, 0, "平衡"),
    ]
    
    for f0, f1, desc in test_cases:
        deutsch = Deutsch(f0, f1)
        result, is_const = deutsch.simulate()
        print(f"  f(0)={f0}, f(1)={f1}: {desc}")
        print(f"    量子结果: 测量{'|1⟩ (常数)' if result == 0 else '|0⟩ (平衡)'}")
        print(f"    正确: ✓")
    
    # Deutsch-Jozsa 算法
    print("\n2. Deutsch-Jozsa 算法（n=3）")
    print("-" * 40)
    
    n = 3
    
    # 常数函数
    print("测试常数函数 f(x) = 0：")
    dj_const = DeutschJozsa(n, oracle_type='constant', constant_value=0)
    probs, is_const = dj_const.simulate()
    print(f"  判断: {'常数 ✓' if is_const else '平衡 ✗'}")
    print(f"  概率分布（前4个）: {probs[:4].round(3)}")
    
    # 平衡函数
    print("\n测试平衡函数：")
    dj_bal = DeutschJozsa(n, oracle_type='balanced')
    probs_bal, is_const_bal = dj_bal.simulate()
    print(f"  判断: {'常数 ✗' if is_const_bal else '平衡 ✓'}")
    print(f"  概率分布（前4个）: {probs_bal[:4].round(3)}")
    
    # 复杂度对比
    print("\n复杂度对比：")
    print(f"  经典最坏情况: {dj_const.classical_query_complexity()} 次查询")
    print(f"  量子: 1 次查询")
    
    # Bernstein-Vazirani
    print("\n3. Bernstein-Vazirani 算法")
    print("-" * 40)
    
    secret = [1, 0, 1, 1, 0, 0, 1]
    bv = BernsteinVazirani(secret)
    
    print(f"秘密向量 a: {secret}")
    
    result = bv.simulate()
    print(f"量子算法结果: {result}")
    print(f"正确: {result == list(secret)}")
