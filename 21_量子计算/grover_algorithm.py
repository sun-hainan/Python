# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / grover_algorithm

本文件实现 grover_algorithm 相关的算法功能。
"""

import numpy as np
import math


# =============================================================================
# Oracle构造 (Oracle Construction)
# =============================================================================

def create_oracle_mark_target(num_qubits, target_index):
    """
    创建Oracle矩阵，标记（翻转）目标状态的振幅
    
    Oracle是一个对角矩阵，对目标状态施加相位翻转
    
    Args:
        num_qubits: 量子比特数n
        target_index: 目标状态的索引 (0 到 2^n-1)
        
    Returns:
        Oracle矩阵 (2^n × 2^n)
    """
    dimension = 2 ** num_qubits
    oracle = np.eye(dimension, dtype=complex)
    # 对目标状态施加-1相位
    oracle[target_index, target_index] = -1
    return oracle


def oracle_phase_kickback(num_qubits, target_bits):
    """
    创建基于比特模式的Oracle（使用相位kickback技巧）
    
    Args:
        num_qubits: 量子比特数
        target_bits: 长度为num_qubits的列表，表示目标比特串
        
    Returns:
        Oracle函数
    """
    def oracle(state_vector):
        """Oracle函数：对满足target_bits的状态施加-1相位"""
        dimension = len(state_vector)
        new_vector = state_vector.copy()
        
        for i in range(dimension):
            # 检查状态i是否匹配目标比特串
            match = True
            for j in range(num_qubits):
                bit = (i >> j) & 1
                if bit != target_bits[j]:
                    match = False
                    break
            if match:
                new_vector[i] *= -1
        return new_vector
    
    return oracle


# =============================================================================
# Diffuser（扩散算子）(Diffusion Operator)
# =============================================================================

def create_diffuser(num_qubits):
    """
    创建Diffuser算子（振幅放大器）
    
    Diffuser = 2|s⟩⟨s| - I，其中|s⟩是均匀叠加态
    
    Diffuser的作用是使所有振幅绕平均振幅翻转，
    从而放大振幅为负（被Oracle标记）的状态
    
    Args:
        num_qubits: 量子比特数
        
    Returns:
        Diffuser矩阵
    """
    dimension = 2 ** num_qubits
    # 均匀叠加态 |s⟩ = (1/√N) Σ|x⟩
    uniform_state = np.ones(dimension, dtype=complex) / np.sqrt(dimension)
    
    # Diffuser = 2|s⟩⟨s| - I
    diffuser = 2 * np.outer(uniform_state, uniform_state.conj()) - np.eye(dimension, dtype=complex)
    return diffuser


# =============================================================================
# Grover算法核心 (Grover Algorithm Core)
# =============================================================================

class GroverSearch:
    """
    Grover搜索算法实现类
    
    Attributes:
        num_qubits: 量子比特数
        num_elements: 搜索空间大小 N = 2^n
        oracle: Oracle（黑盒）函数
        diffuser: Diffuser算子
        optimal_iterations: 最优迭代次数 ≈ √N
    """
    
    def __init__(self, num_qubits, oracle_matrix=None, target_index=None, oracle_func=None):
        """
        初始化Grover搜索
        
        Args:
            num_qubits: 量子比特数
            oracle_matrix: Oracle矩阵（预构建）
            target_index: 目标索引（自动构建Oracle）
            oracle_func: Oracle函数（替代矩阵形式）
        """
        self.num_qubits = num_qubits
        self.num_elements = 2 ** num_qubits
        
        # 构造Oracle
        if oracle_func is not None:
            self.oracle_func = oracle_func
            self.oracle_matrix = None
        elif oracle_matrix is not None:
            self.oracle_matrix = oracle_matrix
            self.oracle_func = None
        elif target_index is not None:
            self.oracle_matrix = create_oracle_mark_target(num_qubits, target_index)
            self.oracle_func = None
        else:
            raise ValueError("必须提供oracle_matrix、target_index或oracle_func之一")
        
        # 创建Diffuser
        self.diffuser = create_diffuser(num_qubits)
        
        # 计算最优迭代次数：⌊π/4 * √N⌋
        self.optimal_iterations = int(math.floor(math.pi / 4 * math.sqrt(self.num_elements)))
    
    def _apply_oracle(self, state_vector):
        """对量子态施加Oracle"""
        if self.oracle_func is not None:
            return self.oracle_func(state_vector)
        else:
            return self.oracle_matrix @ state_vector
    
    def iterate_once(self, state_vector):
        """
        执行一次Grover迭代（Oracle + Diffuser）
        
        Args:
            state_vector: 当前量子态向量
            
        Returns:
            迭代后的量子态向量
        """
        # 步骤1：Oracle - 翻转目标状态的振幅
        state_after_oracle = self._apply_oracle(state_vector)
        
        # 步骤2：Diffuser - 振幅放大
        state_after_diffuser = self.diffuser @ state_after_oracle
        
        return state_after_diffuser
    
    def run(self, num_iterations=None, measure=True):
        """
        运行Grover算法
        
        Args:
            num_iterations: 迭代次数，默认为最优值
            measure: 是否在最后测量
            
        Returns:
            如果measure=True: 返回(测量结果, 概率分布)
            如果measure=False: 返回最终量子态向量
        """
        if num_iterations is None:
            num_iterations = self.optimal_iterations
        
        # 初始叠加态：|s⟩ = (1/√N) Σ|x⟩
        dimension = self.num_elements
        initial_state = np.ones(dimension, dtype=complex) / np.sqrt(dimension)
        
        # 迭代
        current_state = initial_state
        for i in range(num_iterations):
            current_state = self.iterate_once(current_state)
        
        if measure:
            # 测量
            probabilities = np.abs(current_state) ** 2
            measured_index = np.random.choice(dimension, p=probabilities)
            return measured_index, probabilities
        else:
            return current_state
    
    def get_success_probability(self, num_iterations=None):
        """
        获取给定迭代次数下的成功概率
        
        Args:
            num_iterations: 迭代次数
            
        Returns:
            成功概率
        """
        if num_iterations is None:
            num_iterations = self.optimal_iterations
        
        # 计算最终态
        final_state = self.run(num_iterations=num_iterations, measure=False)
        
        # 目标状态的成功概率
        # 注：根据具体Oracle确定目标索引
        success_prob = np.abs(final_state[0]) ** 2  # 假设目标为|0⟩被标记
        
        return success_prob
    
    def print_iteration_info(self):
        """打印算法迭代信息"""
        print(f"量子比特数: {self.num_qubits}")
        print(f"搜索空间大小: N = {self.num_elements}")
        print(f"最优迭代次数: {self.optimal_iterations}")


# =============================================================================
# 多目标搜索Grover算法 (Grover with Multiple Targets)
# =============================================================================

class MultiTargetGrover:
    """
    多目标Grover搜索算法
    
    当有M个目标时，迭代次数约为 √(N/M)
    
    Attributes:
        num_qubits: 量子比特数
        num_targets: 目标数量M
        targets: 目标索引列表
    """
    
    def __init__(self, num_qubits, target_indices):
        """
        初始化多目标Grover搜索
        
        Args:
            num_qubits: 量子比特数
            target_indices: 目标状态索引列表
        """
        self.num_qubits = num_qubits
        self.num_elements = 2 ** num_qubits
        self.targets = target_indices
        self.num_targets = len(target_indices)
        
        # 创建多目标Oracle
        self.oracle_matrix = self._create_multi_target_oracle()
        self.diffuser = create_diffuser(num_qubits)
        
        # 计算最优迭代次数
        self.optimal_iterations = int(math.floor(math.pi / 4 * math.sqrt(self.num_elements / self.num_targets)))
    
    def _create_multi_target_oracle(self):
        """创建多目标Oracle矩阵"""
        dimension = self.num_elements
        oracle = np.eye(dimension, dtype=complex)
        for target in self.targets:
            oracle[target, target] = -1
        return oracle
    
    def run(self, num_iterations=None, measure=True):
        """运行多目标Grover算法"""
        if num_iterations is None:
            num_iterations = self.optimal_iterations
        
        # 初始叠加态
        initial_state = np.ones(self.num_elements, dtype=complex) / np.sqrt(self.num_elements)
        
        # 迭代
        current_state = initial_state
        for _ in range(num_iterations):
            # Oracle
            current_state = self.oracle_matrix @ current_state
            # Diffuser
            current_state = self.diffuser @ current_state
        
        if measure:
            probabilities = np.abs(current_state) ** 2
            measured_index = np.random.choice(self.num_elements, p=probabilities)
            return measured_index, probabilities
        else:
            return current_state


# =============================================================================
# 测试代码 (Test Code)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Grover量子搜索算法测试")
    print("=" * 70)
    
    # 测试1：单目标搜索
    print("\n【测试1】单目标Grover搜索")
    print("搜索空间: N = 8 (3量子比特)")
    print("目标: 状态 |5⟩ (二进制: 101)")
    
    grover = GroverSearch(num_qubits=3, target_index=5)
    grover.print_iteration_info()
    
    print(f"\n执行 {grover.optimal_iterations} 次迭代:")
    result, probs = grover.run(num_iterations=grover.optimal_iterations)
    print(f"测量结果: {result} (二进制: {format(result, '03b')})")
    print(f"成功概率: {probs[5]:.4f}")
    print(f"概率分布: {np.round(probs, 3)}")
    
    # 测试2：多目标搜索
    print("\n" + "-" * 70)
    print("\n【测试2】多目标Grover搜索")
    print("搜索空间: N = 8")
    print("目标: |2⟩ 和 |6⟩ (二进制: 010, 110)")
    
    multi_grover = MultiTargetGrover(num_qubits=3, target_indices=[2, 6])
    print(f"目标数量: M = {multi_grover.num_targets}")
    print(f"最优迭代次数: {multi_grover.optimal_iterations}")
    
    result_multi, probs_multi = multi_grover.run()
    print(f"测量结果: {result_multi}")
    print(f"|2⟩的概率: {probs_multi[2]:.4f}")
    print(f"|6⟩的概率: {probs_multi[6]:.4f}")
    print(f"总成功率: {probs_multi[2] + probs_multi[6]:.4f}")
    
    # 测试3：验证√N复杂度
    print("\n" + "-" * 70)
    print("\n【测试3】验证√N复杂度")
    print("比较不同规模搜索问题所需的迭代次数:")
    
    test_cases = [
        (5, 10),    # N = 32
        (10, 100),  # N = 1024
        (15, 100),  # N = 32768
    ]
    
    for n, target in test_cases:
        grover_test = GroverSearch(num_qubits=n, target_index=target)
        expected = math.floor(math.pi / 4 * math.sqrt(2 ** n))
        print(f"  n={n}, N={2**n}: 最优迭代 ≈ √N = {expected:.1f} (实际: {grover_test.optimal_iterations})")
    
    # 测试4：使用Oracle函数
    print("\n" + "-" * 70)
    print("\n【测试4】使用函数形式Oracle")
    
    def custom_oracle(state):
        """标记所有以'11'结尾的状态"""
        new_state = state.copy()
        dimension = len(state)
        for i in range(dimension):
            if (i & 3) == 3:  # 最后两位为11
                new_state[i] *= -1
        return new_state
    
    grover_func = GroverSearch(num_qubits=4, oracle_func=custom_oracle)
    result_func, probs_func = grover_func.run()
    print(f"目标: 所有以'11'结尾的状态 (3, 7, 11, 15)")
    print(f"测量结果: {result_func} (二进制: {format(result_func, '04b')})")
    print(f"概率分布 (前8个): {np.round(probs_func[:8], 3)}")
    
    # 测试5：振幅分布可视化
    print("\n" + "-" * 70)
    print("\n【测试5】振幅放大过程演示")
    
    grover_demo = GroverSearch(num_qubits=3, target_index=0)
    initial = np.ones(8, dtype=complex) / np.sqrt(8)
    
    print("初始振幅分布:")
    print(f"  振幅: {np.round(initial, 3)}")
    print(f"  概率: {np.round(np.abs(initial)**2, 3)}")
    
    # 一次迭代
    state_after_one = grover_demo.iterate_once(initial)
    print(f"\n1次迭代后的振幅分布:")
    print(f"  振幅: {np.round(state_after_one, 3)}")
    print(f"  概率: {np.round(np.abs(state_after_one)**2, 3)}")
    
    # 完整迭代
    final_state = grover_demo.run(num_iterations=grover_demo.optimal_iterations, measure=False)
    print(f"\n{grover_demo.optimal_iterations}次迭代后的振幅分布:")
    print(f"  振幅: {np.round(final_state, 3)}")
    print(f"  概率: {np.round(np.abs(final_state)**2, 3)}")
    
    print("\n" + "=" * 70)
    print("Grover算法测试完成！")
    print("=" * 70)
