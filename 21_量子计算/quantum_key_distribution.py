# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_key_distribution

本文件实现 quantum_key_distribution 相关的算法功能。
"""

import numpy as np
from collections import Counter


class BB84Protocol:
    """
    BB84 量子密钥分发协议模拟器
    """
    
    def __init__(self, n_bits=100, error_rate=0.0):
        """
        参数：
            n_bits: 要分发的密钥位数
            error_rate: 量子通道错误率（模拟噪声/窃听）
        """
        self.n = n_bits
        self.error_rate = error_rate
        
        # 基类型
        self.BASIS_Z = 0  # 计算基（|0⟩, |1⟩）
        self.BASIS_X = 1  # 对角基（|+⟩, |−⟩）
        
        # 量子态
        # Z 基：|0⟩ = [1,0], |1⟩ = [0,1]
        # X 基：|+⟩ = [1,1]/math.sqrt(2), |−⟩ = [1,-1]/math.sqrt(2)
    
    def alice_generate(self):
        """Alice：生成随机比特串和基"""
        self.alice_bits = np.random.randint(0, 2, self.n)
        self.alice_basis = np.random.randint(0, 2, self.n)
        return self.alice_bits, self.alice_basis
    
    def alice_prepare_qubit(self, bit, basis):
        """
        Alice：根据比特和基制备量子态
        
        返回：量子态向量
        """
        if basis == self.BASIS_Z:
            if bit == 0:
                return np.array([1, 0], dtype=complex)  # |0⟩
            else:
                return np.array([0, 1], dtype=complex)  # |1⟩
        else:  # X basis
            if bit == 0:
                return np.array([1, 1], dtype=complex) / np.sqrt(2)  # |+⟩
            else:
                return np.array([1, -1], dtype=complex) / np.sqrt(2)  # |−⟩
    
    def bob_measure(self, qubit, basis):
        """
        Bob：测量量子态
        
        返回：测量结果比特
        """
        if basis == self.BASIS_Z:
            # Z 基测量
            probs = np.abs(qubit) ** 2
            result = np.random.choice(2, p=probs)
        else:
            # X 基测量
            plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
            minus = np.array([1, -1], dtype=complex) / np.sqrt(2)
            
            p_plus = np.abs(np.conj(plus) @ qubit) ** 2
            result = np.random.choice(2, p=[p_plus, 1-p_plus])
        
        return result
    
    def channel_noise(self, qubit):
        """
        量子通道噪声（也模拟窃听）
        
        以一定概率翻转比特
        """
        if np.random.random() < self.error_rate:
            # 添加噪声（比特翻转）
            if np.random.random() < 0.5:
                return np.array([0, 1], dtype=complex)  # flip |0⟩ -> |1⟩
            else:
                return np.array([1, 0], dtype=complex)
        return qubit
    
    def bob_generate(self):
        """Bob：随机选择测量基并测量"""
        self.bob_basis = np.random.randint(0, 2, self.n)
        self.bob_bits = np.zeros(self.n, dtype=int)
        
        for i in range(self.n):
            # Alice 发送的态
            alice_qubit = self.alice_prepare_qubit(
                self.alice_bits[i], self.alice_basis[i])
            
            # 通道噪声
            noisy_qubit = self.channel_noise(alice_qubit)
            
            # Bob 测量
            self.bob_bits[i] = self.bob_measure(noisy_qubit, self.bob_basis[i])
        
        return self.bob_bits, self.bob_basis
    
    def sift_key(self):
        """
        筛选（Sifting）
        
        保留基匹配的比特
        """
        matching = self.alice_basis == self.bob_basis
        n_matching = np.sum(matching)
        
        self.sifted_alice = self.alice_bits[matching]
        self.sifted_bob = self.bob_bits[matching]
        
        return n_matching, self.sifted_alice, self.sifted_bob
    
    def error_rate_check(self, n_check=20):
        """
        错误率检测（随机抽样）
        
        从筛选后的密钥中随机抽取一部分公开比较
        """
        if len(self.sifted_alice) < n_check:
            n_check = len(self.sifted_alice)
        
        if n_check == 0:
            return 0, []
        
        # 随机选择检查位置
        check_indices = np.random.choice(
            len(self.sifted_alice), n_check, replace=False)
        
        errors = 0
        check_positions = []
        
        for idx in check_indices:
            alice_bit = self.sifted_alice[idx]
            bob_bit = self.sifted_bob[idx]
            
            if alice_bit != bob_bit:
                errors += 1
            
            check_positions.append(idx)
        
        error_rate = errors / n_check
        
        # 移除检查位置
        mask = np.ones(len(self.sifted_alice), dtype=bool)
        mask[check_positions] = False
        
        self.final_key_alice = self.sifted_alice[mask]
        self.final_key_bob = self.sifted_bob[mask]
        
        return error_rate, check_positions
    
    def key_agreement(self):
        """完整的密钥协商过程"""
        # Alice 和 Bob 生成比特
        self.alice_generate()
        self.bob_generate()
        
        # 筛选
        n_matching, sifted_alice, sifted_bob = self.sift_key()
        
        # 错误率检测
        error_rate, check_pos = self.error_rate_check(n_check=min(30, n_matching))
        
        # 判断安全性
        secure = error_rate < 0.15  # 15% 阈值
        
        return {
            'n_matching': n_matching,
            'error_rate': error_rate,
            'secure': secure,
            'final_key_length': len(self.final_key_alice),
            'final_key_alice': self.final_key_alice,
            'final_key_bob': self.final_key_bob,
        }


def simulate_eavesdropper(bb84, eavesdrop_strategy='measure'):
    """
    模拟窃听者 Eve
    
    窃听策略：
    1. 'measure': 随机基测量
    2. 'intercept_resend': 拦截重发
    """
    bb84.error_rate = 0.25  # Eve 的存在增加错误率
    
    if eavesdrop_strategy == 'intercept_resend':
        # Eve 拦截并测量，然后重发
        # 这会引入 25% 的错误率（当使用随机基时）
        bb84.error_rate = 0.25


if __name__ == "__main__":
    print("=" * 55)
    print("BB84 量子密钥分发协议")
    print("=" * 55)
    
    # 无窃听场景
    print("\n场景 1：无窃听（理想通道）")
    print("-" * 40)
    
    bb84 = BB84Protocol(n_bits=100, error_rate=0.0)
    result = bb84.key_agreement()
    
    print(f"基匹配数量: {result['n_matching']}/100")
    print(f"错误率: {result['error_rate']*100:.1f}%")
    print(f"安全: {result['secure']}")
    print(f"最终密钥长度: {result['final_key_length']}")
    
    if result['secure']:
        key_match = np.array_equal(
            result['final_key_alice'], result['final_key_bob'])
        print(f"密钥一致: {key_match}")
    
    # 有窃听场景
    print("\n场景 2：窃听者存在（拦截重发攻击）")
    print("-" * 40)
    
    bb84_eve = BB84Protocol(n_bits=100, error_rate=0.25)
    result_eve = bb84_eve.key_agreement()
    
    print(f"错误率: {result_eve['error_rate']*100:.1f}%")
    print(f"安全: {result_eve['secure']}")
    
    if result_eve['error_rate'] > 0.15:
        print("⚠️ 检测到可能的窃听！")
    
    # 高噪声通道（但无窃听）
    print("\n场景 3：高噪声通道（无窃听）")
    print("-" * 40)
    
    bb84_noise = BB84Protocol(n_bits=100, error_rate=0.08)
    result_noise = bb84_noise.key_agreement()
    
    print(f"通道错误率: 8%")
    print(f"检测错误率: {result_noise['error_rate']*100:.1f}%")
    print(f"安全: {result_noise['secure']}")
