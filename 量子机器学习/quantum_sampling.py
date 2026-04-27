# -*- coding: utf-8 -*-

"""

算法实现：量子机器学习 / quantum_sampling



本文件实现 quantum_sampling 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional, Set

from dataclasses import dataclass

from enum import Enum

import itertools





class Sampling_Type(Enum):

    """采样类型"""

    BOSON_SAMPLING = "boson_sampling"

    GAUSSIAN_BOSON_SAMPLING = "gaussian_boson_sampling"

    QUANTUM_MONTE_CARLO = "quantum_monte_carlo"





@dataclass

class Photon_Configuration:

    """光子配置"""

    num_modes: int

    photon_counts: List[int]  # 每个模式的光子数





@dataclass

class Interferometer_Matrix:

    """干涉仪矩阵（幺正矩阵）"""

    matrix: np.ndarray

    num_modes: int





class Fock_Space:

    """Fock空间（光子数空间）"""

    def __init__(self, num_modes: int, max_photons_per_mode: int = 4):

        self.num_modes = num_modes

        self.max_photons = max_photons_per_mode

        # 总光子数上限

        self.max_total_photons = num_modes * max_photons_per_mode





    def enumerate_states(self, total_photons: int) -> List[List[int]]:

        """枚举给定总光子数的所有Fock态"""

        # 生成所有可能的分布

        if total_photons == 0:

            return [([0] * self.num_modes)]

        states = []

        for comb in itertools.combinations_with_replacement(range(self.num_modes), total_photons):

            state = [0] * self.num_modes

            for mode in comb:

                state[mode] += 1

            states.append(state)

        return states





    def state_to_index(self, state: List[int]) -> int:

        """将Fock态转换为索引（用于查找表）"""

        index = 0

        for i, count in enumerate(state):

            index = index * (self.max_photons + 1) + count

        return index





class Boson_Sampling_Simulator:

    """Boson Sampling模拟器"""

    def __init__(self, num_modes: int = 6, num_photons: int = 4):

        self.num_modes = num_modes

        self.num_photons = num_photons

        self.fock_space = Fock_Space(num_modes)

        self.interferometer: Optional[Interferometer_Matrix] = None





    def set_interferometer(self, matrix: np.ndarray):

        """设置干涉仪矩阵"""

        if matrix.shape[0] != matrix.shape[1] or matrix.shape[0] != self.num_modes:

            raise ValueError(f"干涉仪矩阵必须是 {self.num_modes}x{self.num_modes}")

        self.interferometer = Interferometer_Matrix(matrix=matrix, num_modes=self.num_modes)





    def compute_interference_probability(self, input_state: List[int], output_state: List[int]) -> float:

        """

        计算干涉概率

        P(output|input) = |⟨output|U|input⟩|²

        使用Permanents计算

        """

        if self.interferometer is None:

            raise ValueError("干涉仪未设置")

        U = self.interferometer.matrix

        # 简化的概率计算（实际需要计算Permanent）

        # 对于小矩阵可以使用莱布尼茨公式

        n = self.num_photons

        if n == 0:

            return 1.0 if sum(output_state) == 0 else 0.0

        # 创建子矩阵

        submatrix_rows = []

        submatrix_cols = []

        # 行对应输入模式

        for mode, count in enumerate(input_state):

            submatrix_rows.extend([mode] * count)

        # 列对应输出模式

        for mode, count in enumerate(output_state):

            submatrix_cols.extend([mode] * count)

        if len(submatrix_rows) != len(submatrix_cols):

            return 0.0

        submatrix = U[np.ix_(submatrix_rows, submatrix_cols)]

        # 计算Permanent（简化：使用小矩阵的显式公式）

        perm = self._compute_permanent(submatrix)

        probability = np.abs(perm) ** 2

        return probability





    def _compute_permanent(self, matrix: np.ndarray) -> complex:

        """计算矩阵的Permanent（简化实现）"""

        n = matrix.shape[0]

        if n == 1:

            return matrix[0, 0]

        if n == 2:

            return matrix[0, 0] * matrix[1, 1] + matrix[0, 1] * matrix[1, 0]

        if n == 3:

            result = 0.0

            for perm in itertools.permutations(range(3)):

                prod = matrix[0, perm[0]] * matrix[1, perm[1]] * matrix[2, perm[2]]

                result += prod

            return result

        # 对于更大的矩阵，使用Ryser算法（简化）

        return self._compute_permanent_ryser(matrix)





    def _compute_permanent_ryser(self, matrix: np.ndarray) -> complex:

        """Ryser算法计算Permanent"""

        n = matrix.shape[0]

        total = 0.0

        for subset in range(1 << n):

            sgn = -1 if bin(subset).count('1') % 2 else 1

            prod = 1.0

            for row in range(n):

                row_sum = 0.0

                for col in range(n):

                    if (subset >> col) & 1:

                        row_sum += matrix[row, col]

                prod *= row_sum

            total += sgn * prod

        return complex(total * ((-1) ** n))





    def sample(self, input_state: List[int] = None) -> List[int]:

        """

        采样输出光子配置

        使用概率分布采样

        """

        if input_state is None:

            input_state = [1] * self.num_photons + [0] * (self.num_modes - self.num_photons)

        # 枚举所有可能的输出态

        output_states = self.fock_space.enumerate_states(self.num_photons)

        probabilities = []

        for state in output_states:

            prob = self.compute_interference_probability(input_state, state)

            probabilities.append(prob)

        # 归一化

        total = sum(probabilities)

        if total > 0:

            probabilities = [p / total for p in probabilities]

        else:

            probabilities = [1.0 / len(output_states)] * len(output_states)

        # 采样

        idx = np.random.choice(len(output_states), p=probabilities)

        return output_states[idx]





class Gaussian_Boson_Sampling:

    """高斯玻色采样（简化）"""

    def __init__(self, num_modes: int = 6):

        self.num_modes = num_modes

        self.mean_photon_number: float = 0.0





    def set_mean_photon_number(self, mu: float):

        """设置平均光子数"""

        self.mean_photon_number = mu





    def sample(self) -> List[int]:

        """从热分布采样光子数"""

        # 简化的热分布采样

        output = []

        for _ in range(self.num_modes):

            # 简化的泊松采样

            n = np.random.poisson(self.mean_photon_number / self.num_modes)

            output.append(n)

        return output





def create_random_interferometer(num_modes: int) -> np.ndarray:

    """创建随机幺正干涉仪矩阵（Haar随机）"""

    # 生成随机复数矩阵

    Z = np.random.randn(num_modes, num_modes) + 1j * np.random.randn(num_modes, num_modes)

    # QR分解得到幺正矩阵

    Q, R = np.linalg.qr(Z)

    # 调整相位

    D = np.diag(R) / np.abs(np.diag(R))

    U = Q @ np.diag(D)

    return U





def basic_test():

    """基本功能测试"""

    print("=== 量子采样与Boson Sampling测试 ===")

    # 创建干涉仪

    num_modes = 4

    num_photons = 2

    print(f"模式数: {num_modes}, 光子数: {num_photons}")

    U = create_random_interferometer(num_modes)

    print(f"干涉仪矩阵:\n{U}")

    # Boson Sampling

    print("\n[Boson Sampling]")

    sampler = Boson_Sampling_Simulator(num_modes=num_modes, num_photons=num_photons)

    sampler.set_interferometer(U)

    # 测试单个概率

    input_state = [1, 1, 0, 0]  # 两个光子分别进入模式0和1

    print(f"输入态: {input_state}")

    # 枚举输出态并计算概率

    fock_space = Fock_Space(num_modes)

    output_states = fock_space.enumerate_states(num_photons)

    probabilities = []

    for state in output_states[:5]:  # 只显示前5个

        prob = sampler.compute_interference_probability(input_state, state)

        probabilities.append((state, prob))

        print(f"  输出{state}: 概率 = {prob:.6f}")

    # 采样测试

    print("\n采样100次:")

    samples = []

    for _ in range(100):

        sample = sampler.sample(input_state)

        samples.append(tuple(sample))

    # 统计

    from collections import Counter

    sample_counts = Counter(samples)

    print("  采样分布（显示前5个）:")

    for state, count in sample_counts.most_common(5):

        print(f"    {list(state)}: {count}次")

    # 高斯玻色采样

    print("\n[高斯玻色采样]")

    gbs = Gaussian_Boson_Sampling(num_modes=6)

    gbs.set_mean_photon_number(mu=3.0)

    print(f"平均光子数: {gbs.mean_photon_number}")

    print("采样10次:")

    for i in range(10):

        sample = gbs.sample()

        print(f"  样本{i+1}: {sample}, 总光子数: {sum(sample)}")





if __name__ == "__main__":

    basic_test()

