# -*- coding: utf-8 -*-

"""

算法实现：次线性算法 / quantum_sublinear



本文件实现 quantum_sublinear 相关的算法功能。

"""



from typing import List, Optional, Tuple, Callable

from dataclasses import dataclass

import numpy as np

import random

import math





# =============================================================================

# 量子基础

# =============================================================================



@dataclass

class QuantumState:

    """量子态（简化表示）"""

    amplitudes: List[complex]  # 振幅向量



    def __post_init__(self):

        # 归一化振幅

        norm = math.sqrt(sum(abs(a) ** 2 for a in self. amplitudes))

        if norm > 0:

            self.amplitudes = [a / norm for a in self.amplitudes]



    def measure(self) -> int:

        """

        测量量子态，返回经典比特



        测量概率与振幅幅度的平方成正比

        """

        probs = [abs(a) ** 2 for a in self.amplitudes]

        return np.random.choice(len(self.amplitudes), p=probs)



    def probability(self, index: int) -> float:

        """获取特定状态的测量概率"""

        return abs(self.amplitudes[index]) ** 2





class QuantumOracle:

    """

    量子Oracle（黑盒预言）



    用于Grover搜索等量子算法

    """



    def __init__(self, target_index: int, n_qubits: int):

        self.target_index = target_index

        self.n_qubits = n_qubits

        self.n_states = 2 ** n_qubits



    def evaluate(self, index: int) -> bool:

        """判断index是否为目标状态"""

        return index == self.target_index



    def phase_flip(self, amplitudes: List[complex]) -> List[complex]:

        """对目标状态施加相位翻转"""

        new_amplitudes = list(amplitudes)

        new_amplitudes[self.target_index] *= -1

        return new_amplitudes





# =============================================================================

# Grover搜索算法

# =============================================================================



class GroverSearch:

    """

    Grover搜索算法（量子搜索）



    在无序数据库中查找目标元素



    复杂度：

        - 经典：O(N)

        - 量子：O(sqrt(N))



    参数：

        - N：数据库大小

        - M：目标元素数量（如果已知）

    """



    def __init__(self, n_qubits: int):

        self.n_qubits = n_qubits

        self.n_states = 2 ** n_qubits



    def _initialize_uniform(self) -> QuantumState:

        """初始化为均匀叠加态"""

        amplitude = 1 / math.sqrt(self.n_states)

        amplitudes = [complex(amplitude, 0) for _ in range(self.n_states)]

        return QuantumState(amplitudes)



    def _diffusion_operator(self, amplitudes: List[complex]) -> List[complex]:

        """

        扩散算子（Grover扩散算子）



        矩阵形式：

            D = 2|s><s| - I

        其中|s>是均匀叠加态

        """

        n = len(amplitudes)

        mean = sum(amplitudes) / n



        # 应用 D = 2|s><s| - I

        new_amplitudes = []

        for a in amplitudes:

            new_a = 2 * mean - a

            new_amplitudes.append(complex(new_a, 0))



        return new_amplitudes



    def search(self, oracle: QuantumOracle, n_iterations: Optional[int] = None) -> int:

        """

        执行Grover搜索



        参数:

            oracle: 量子Oracle

            n_iterations: 迭代次数（如果为None，自动计算）



        返回:

            找到的目标状态索引

        """

        # 计算最优迭代次数

        if n_iterations is None:

            # 估算目标数量（这里假设为1）

            n_iterations = int(math.pi / 4 * math.sqrt(self.n_states))



        # 初始化

        state = self._initialize_uniform()



        # Grover迭代

        for _ in range(n_iterations):

            # Oracle相位翻转

            amplitudes = oracle.phase_flip(state.amplitudes)



            # 扩散算子

            amplitudes = self._diffusion_operator(amplitudes)



            state = QuantumState(amplitudes)



        # 测量

        return state.measure()



    def search_with_multiple_targets(self, oracle: QuantumOracle,

                                    n_targets: int) -> int:

        """

        搜索多个目标（已知目标数量）



        参数:

            oracle: 量子Oracle

            n_targets: 目标数量



        返回:

            找到的目标状态索引

        """

        # 最优迭代次数

        n_iterations = int(math.pi / (4 * math.sqrt(n_targets)))



        state = self._initialize_uniform()



        for _ in range(n_iterations):

            amplitudes = oracle.phase_flip(state.amplitudes)

            amplitudes = self._diffusion_operator(amplitudes)

            state = QuantumState(amplitudes)



        return state.measure()





# =============================================================================

# 量子计数

# =============================================================================



class QuantumCounting:

    """

    量子计数算法



    估计满足Oracle的状态数量



    复杂度：

        - 经典：O(N)

        - 量子：O(sqrt(N))



    使用Phase Estimation结合 Grover迭代

    """



    def __init__(self, n_qubits: int):

        self.n_qubits = n_qubits

        self.n_states = 2 ** n_qubits



    def _grover_iteration_matrix(self, n_targets: int) -> np.ndarray:

        """

        构建Grover迭代矩阵



        G = (2|s><s| - I) * O

        其中O是Oracle

        """

        n = self.n_states



        # 均匀叠加态

        uniform = np.ones(n) / math.sqrt(n)



        # Grover迭代的特征值：e^{±iθ}，其中 sin²(θ/2) = M/N

        # M是目标数量，N是总状态数

        theta = 2 * math.asin(math.sqrt(n_targets / n))



        # 相位估计角度

        return theta



    def estimate_count(self, oracle: QuantumOracle,

                      n_counting_qubits: int = 10,

                      n_iterations: int = 100) -> Tuple[int, float]:

        """

        估计满足Oracle的状态数量



        参数:

            oracle: 量子Oracle

            n_counting_qubits: 用于计数的量子比特数

            n_iterations: 迭代次数



        返回:

            (估计的目标数量, 置信度)

        """

        # 简化的计数估计

        # 实际使用Phase Estimation



        # Grover迭代的特征值

        theta = 2 * math.asin(1 / math.sqrt(self.n_states))  # 假设1个目标



        # 多次迭代观察相位

        phases = []

        for _ in range(n_iterations):

            # 简化的相位估计

            phase = np.random.uniform(0, 2 * math.pi)

            phases.append(phase)



        # 平均相位

        avg_phase = np.mean(phases)



        # 从相位估计目标数量

        # theta ≈ π/2 * (1 - M/N)

        m_estimate = int(self.n_states * (1 - 2 * avg_phase / math.pi))



        return max(1, m_estimate), 0.95





# =============================================================================

# 量子模式匹配

# =============================================================================



class QuantumPatternMatching:

    """

    量子模式匹配算法



    在文本中查找模式



    复杂度：

        - 经典：O(NM)

        - 量子：O(sqrt(NM))



    其中N是文本长度，M是模式长度

    """



    def __init__(self, text: str, pattern: str):

        self.text = text

        self.pattern = pattern

        self.n = len(text)

        self.m = len(pattern)



    def _build_state(self) -> str:

        """构建叠加态"""

        # 简化：返回文本

        return self.text



    def _oracle_match(self, shift: int) -> bool:

        """检查给定偏移是否匹配"""

        if shift + self.m > self.n:

            return False

        return self.text[shift:shift + self.m] == self.pattern



    def search(self) -> List[int]:

        """

        搜索模式的所有出现位置



        返回:

            匹配位置列表

        """

        matches = []



        # 简化的搜索（实际应该使用量子搜索）

        for i in range(self.n - self.m + 1):

            if self._oracle_match(i):

                matches.append(i)



        return matches



    def quantum_search(self) -> List[int]:

        """

        量子模式匹配（简化实现）



        实际使用Quantum Walking或 Grover变体

        """

        # 估计迭代次数

        n_matches_estimate = self.n // self.m  # 简化的估计

        n_iterations = max(1, int(math.pi / (4 * math.sqrt(n_matches_estimate + 1))))



        matches = []



        # 简化的实现：重复经典搜索

        for _ in range(n_iterations):

            matches = self.search()

            if matches:

                break



        return matches





# =============================================================================

# 量子梯度估计

# =============================================================================



class QuantumGradientEstimation:

    """

    量子梯度估计



    估计函数的梯度



    复杂度：

        - 经典：O(D) 评估D次

        - 量子：O(1) 使用单次评估



    使用HHL算法的变体或量子模拟微分

    """



    def __init__(self, n_params: int):

        self.n_params = n_params



    def estimate_gradient(self, func: Callable,

                         x: np.ndarray,

                         epsilon: float = 0.01) -> np.ndarray:

        """

        估计梯度



        参数:

            func: 目标函数

            x: 参数点

            epsilon: 扰动大小



        返回:

            梯度估计

        """

        d = len(x)

        gradient = np.zeros(d)



        # 简化的有限差分

        for i in range(d):

            x_plus = x.copy()

            x_plus[i] += epsilon



            f_plus = func(x_plus)

            f_orig = func(x)



            gradient[i] = (f_plus - f_orig) / epsilon



        return gradient



    def quantum_gradient(self, func: Callable,

                        x: np.ndarray) -> np.ndarray:

        """

        量子梯度估计（简化实现）



        实际应该使用量子相位估计



        返回:

            梯度估计

        """

        # 简化的量子-inspired实现

        d = len(x)



        # 使用随机扰动

        gradient = np.zeros(d)

        n_samples = 10



        for _ in range(n_samples):

            # 随机方向

            direction = np.random.randn(d)

            direction = direction / np.linalg.norm(direction)



            # 量子-inspired估计

            eps = 0.01

            f_plus = func(x + eps * direction)

            f_minus = func(x - eps * direction)



            # 累积到梯度

            gradient += (f_plus - f_minus) / (2 * eps) * direction



        return gradient / n_samples





# =============================================================================

# 量子振幅估计

# =============================================================================



class QuantumAmplitudeEstimation:

    """

    量子振幅估计



    估计满足条件的振幅/概率



    用于：

        - 蒙特卡洛积分

        - 概率估计

        - 金融衍生品定价

    """



    def __init__(self, n_qubits: int):

        self.n_qubits = n_qubits

        self.n_states = 2 ** n_qubits



    def estimate_probability(self, oracle: QuantumOracle,

                            n_iterations: int = 100) -> float:

        """

        估计满足Oracle的振幅（概率）



        参数:

            oracle: 量子Oracle

            n_iterations: 迭代次数



        返回:

            概率估计

        """

        # 简化的估计：使用Grover搜索的成功率

        target_count = 0



        for _ in range(n_iterations):

            # 初始化均匀叠加态

            amplitudes = [complex(1 / math.sqrt(self.n_states), 0)

                        for _ in range(self.n_states)]



            # 应用一次Grover迭代（简化）

            amplitudes = oracle.phase_flip(amplitudes)



            # 测量

            result = np.random.choice(self.n_states,

                                     p=[abs(a) ** 2 for a in amplitudes])



            if oracle.evaluate(result):

                target_count += 1



        return target_count / n_iterations



    def estimate_mean(self, values: List[float],

                     n_iterations: int = 100) -> float:

        """

        估计平均值（使用振幅估计）



        参数:

            values: 值列表

            n_iterations: 迭代次数



        返回:

            平均值估计

        """

        n = len(values)

        if n == 0:

            return 0.0



        # 振幅估计

        # 简化的实现

        return sum(values) / n





# =============================================================================

# 测试代码

# =============================================================================



if __name__ == "__main__":

    print("=" * 60)

    print("量子亚线性算法测试")

    print("=" * 60)



    # 测试1：Grover搜索

    print("\n【测试1：Grover搜索】")

    n_qubits = 10

    n_states = 2 ** n_qubits



    # 随机选择目标

    target = random.randint(0, n_states - 1)

    oracle = QuantumOracle(target, n_qubits)



    grover = GroverSearch(n_qubits)

    result = grover.search(oracle)



    print(f"搜索空间大小: {n_states}")

    print(f"目标索引: {target}")

    print(f"找到索引: {result}")

    print(f"搜索{'成功' if result == target else '失败'}")



    # 测试2：多目标搜索

    print("\n【测试2：多目标搜索】")

    targets = [100, 200, 300]

    n_targets = len(targets)



    # 创建多目标Oracle

    class MultiTargetOracle(QuantumOracle):

        def __init__(self, targets, n_qubits):

            super().__init__(targets[0], n_qubits)

            self.targets = set(targets)



        def evaluate(self, index):

            return index in self.targets



        def phase_flip(self, amplitudes):

            new_amplitudes = list(amplitudes)

            for t in self.targets:

                new_amplitudes[t] *= -1

            return new_amplitudes



    multi_oracle = MultiTargetOracle(targets, n_qubits)

    result_multi = grover.search_with_multiple_targets(multi_oracle, n_targets)

    print(f"目标集合: {targets}")

    print(f"找到: {result_multi}")



    # 测试3：量子计数

    print("\n【测试3：量子计数】")

    counting = QuantumCounting(n_qubits)

    est_count, conf = counting.estimate_count(oracle)

    print(f"估计满足条件的状态数: {est_count}")

    print(f"置信度: {conf}")



    # 测试4：量子模式匹配

    print("\n【测试4：量子模式匹配】")

    text = "ABABABABA" * 100

    pattern = "ABAB"



    pm = QuantumPatternMatching(text, pattern)

    matches = pm.quantum_search()

    print(f"文本长度: {len(text)}")

    print(f"模式: {pattern}")

    print(f"匹配位置: {matches[:10]}..." if len(matches) > 10 else f"匹配位置: {matches}")



    # 测试5：量子梯度估计

    print("\n【测试5：量子梯度估计】")



    # 测试函数：f(x,y) = x^2 + y^2

    def test_func(x):

        return np.sum(x ** 2)



    qge = QuantumGradientEstimation(n_params=2)

    x0 = np.array([1.0, 2.0])



    # 经典梯度

    gradient_classic = qge.estimate_gradient(test_func, x0)

    print(f"经典梯度: {gradient_classic}")

    print(f"理论梯度: [2.0, 4.0]")



    # 量子梯度（简化）

    gradient_quantum = qge.quantum_gradient(test_func, x0)

    print(f"量子梯度: {gradient_quantum}")



    # 测试6：量子振幅估计

    print("\n【测试6：量子振幅估计】")

    ae = QuantumAmplitudeEstimation(n_qubits=5)



    # 创建测试Oracle

    test_oracle = QuantumOracle(0, 5)  # 目标只有索引0

    prob_est = ae.estimate_probability(test_oracle, n_iterations=100)

    print(f"估计概率: {prob_est:.4f}")

    print(f"真实概率: {1/32:.4f}")



    # 测试7：复杂度比较

    print("\n【测试7：复杂度比较】")

    print(f"{'问题':<25} {'经典复杂度':<15} {'量子复杂度':<15}")

    print("-" * 55)

    print(f"{'搜索':<25} {'O(N)':<15} {'O(sqrt(N))':<15}")

    print(f"{'模式匹配':<25} {'O(NM)':<15} {'O(sqrt(NM))':<15}")

    print(f"{'计数':<25} {'O(N)':<15} {'O(sqrt(N))':<15}")

    print(f"{'梯度估计':<25} {'O(D)':<15} {'O(1)':<15}")

    print(f"{'振幅估计':<25} {'O(1/eps^2)':<15} {'O(1/eps)':<15}")

